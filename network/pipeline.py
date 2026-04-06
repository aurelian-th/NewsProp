from __future__ import annotations

from runtime_bootstrap import patch_windows_platform

patch_windows_platform()

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from .calibration import SOURCES, MoldovaCalibration, default_calibration


@dataclass
class Phase3NetworkConfig:
    node_count: int = 1000
    attach_edges_m: int = 3
    seed: int = 20260401
    hub_top_fraction: float = 0.05
    output_dir: str = "outputs/phase3_network"
    betweenness_k: int | None = None
    eigenvector_max_iter: int = 1000
    eigenvector_tol: float = 1e-6


@dataclass
class Phase3Artifacts:
    output_dir: Path
    graphml_path: Path
    adjacency_path: Path
    agents_csv_path: Path
    agents_json_path: Path
    edges_csv_path: Path
    mesa_payload_path: Path
    summary_path: Path


def _normalize_array(values: np.ndarray) -> np.ndarray:
    lo = float(np.min(values))
    hi = float(np.max(values))
    if math.isclose(hi, lo):
        return np.zeros_like(values, dtype=float)
    return (values - lo) / (hi - lo)


def _gini(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    v = np.sort(values.astype(float))
    if np.allclose(v, 0.0):
        return 0.0
    n = v.size
    cumulative = np.cumsum(v)
    return float((n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n)


def _sample_truncated_normal_int(
    rng: np.random.Generator,
    size: int,
    mean: float,
    std: float,
    low: int,
    high: int,
) -> np.ndarray:
    sampled = rng.normal(loc=mean, scale=std, size=size)
    clipped = np.clip(sampled, low, high)
    return np.rint(clipped).astype(int)


def build_scale_free_graph(config: Phase3NetworkConfig) -> nx.Graph:
    if config.node_count < 2:
        raise ValueError("node_count must be >= 2")
    if config.attach_edges_m < 1 or config.attach_edges_m >= config.node_count:
        raise ValueError("attach_edges_m must satisfy 1 <= m < node_count")

    return nx.barabasi_albert_graph(
        n=config.node_count,
        m=config.attach_edges_m,
        seed=config.seed,
    )


def _sample_channel_for_agent(age: int, has_internet: bool, rng: np.random.Generator) -> str:
    if age < 30:
        probs = {"Social": 0.72, "TV": 0.12, "Mouth": 0.16}
    elif age < 50:
        probs = {"Social": 0.58, "TV": 0.24, "Mouth": 0.18}
    elif age < 65:
        probs = {"Social": 0.38, "TV": 0.44, "Mouth": 0.18}
    else:
        probs = {"Social": 0.24, "TV": 0.58, "Mouth": 0.18}

    if not has_internet:
        probs["Social"] *= 0.2
        probs["TV"] += 0.30
        probs["Mouth"] += 0.20

    total = sum(probs.values())
    channels = list(probs)
    weights = [probs[k] / total for k in channels]
    return str(rng.choice(channels, p=weights))


def build_agent_profiles(
    graph: nx.Graph,
    calibration: MoldovaCalibration,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    node_ids = np.array(sorted(graph.nodes()), dtype=int)
    n = len(node_ids)

    is_urban = rng.random(n) < calibration.urban_share_2024
    has_internet = rng.random(n) < calibration.internet_users_share_2023

    is_senior = rng.random(n) < calibration.age_share_65_80
    ages_working = _sample_truncated_normal_int(rng, n, mean=42.0, std=12.0, low=18, high=64)
    ages_senior = _sample_truncated_normal_int(rng, n, mean=71.0, std=5.0, low=65, high=80)
    ages = np.where(is_senior, ages_senior, ages_working)

    channels = np.array(
        [_sample_channel_for_agent(int(age), bool(net), rng) for age, net in zip(ages, has_internet)],
        dtype=object,
    )

    age_penalty = np.maximum(ages - 55, 0) / 120.0
    critical = 0.52 + is_urban * 0.06 + has_internet * 0.05 - age_penalty + rng.normal(0.0, 0.12, n)
    critical = np.clip(critical, 0.0, 1.0)

    tv_bonus = np.where(channels == "TV", 0.14, 0.0)
    social_penalty = np.where(channels == "Social", 0.04, 0.0)
    age_bonus = np.clip((ages - 40) / 100.0, 0.0, 0.22)
    trust = 0.44 + tv_bonus + age_bonus - social_penalty + rng.normal(0.0, 0.14, n)
    trust = np.clip(trust, 0.0, 1.0)

    profiles = pd.DataFrame(
        {
            "node_id": node_ids,
            "age": ages.astype(int),
            "critical_thinking": critical.astype(float),
            "media_trust": trust.astype(float),
            "preferred_channel": channels.astype(str),
            "urban": is_urban.astype(bool),
            "internet_access": has_internet.astype(bool),
        }
    )

    return profiles


def compute_centrality_metrics(
    graph: nx.Graph,
    config: Phase3NetworkConfig,
) -> pd.DataFrame:
    n = graph.number_of_nodes()
    betweenness_k = config.betweenness_k

    if betweenness_k is None and n > 2500:
        betweenness_k = min(512, n)

    if betweenness_k is None:
        betweenness = nx.betweenness_centrality(graph, normalized=True)
    else:
        betweenness = nx.betweenness_centrality(
            graph,
            k=betweenness_k,
            normalized=True,
            seed=config.seed,
        )

    try:
        eigenvector = nx.eigenvector_centrality(
            graph,
            max_iter=config.eigenvector_max_iter,
            tol=config.eigenvector_tol,
        )
    except nx.PowerIterationFailedConvergence:
        eigenvector = nx.eigenvector_centrality_numpy(graph)

    node_ids = np.array(sorted(graph.nodes()), dtype=int)
    b_values = np.array([float(betweenness[nid]) for nid in node_ids], dtype=float)
    e_values = np.array([float(eigenvector[nid]) for nid in node_ids], dtype=float)

    b_norm = _normalize_array(b_values)
    e_norm = _normalize_array(e_values)
    influence = 0.5 * b_norm + 0.5 * e_norm

    return pd.DataFrame(
        {
            "node_id": node_ids,
            "betweenness": b_values,
            "eigenvector": e_values,
            "influence_score": influence,
        }
    )


def tag_hubs(metrics_df: pd.DataFrame, hub_top_fraction: float) -> pd.DataFrame:
    if not (0.0 < hub_top_fraction <= 1.0):
        raise ValueError("hub_top_fraction must be in (0, 1]")

    out = metrics_df.copy()
    hub_count = max(1, int(math.ceil(len(out) * hub_top_fraction)))
    out["hub_node"] = False

    top_idx = out.nlargest(hub_count, "influence_score").index
    out.loc[top_idx, "hub_node"] = True

    return out


def _attach_node_attributes(graph: nx.Graph, merged_df: pd.DataFrame) -> None:
    attrs: dict[int, dict[str, Any]] = {}
    for row in merged_df.itertuples(index=False):
        node_id = int(row.node_id)
        attrs[node_id] = {
            "age": int(row.age),
            "critical_thinking": float(row.critical_thinking),
            "media_trust": float(row.media_trust),
            "preferred_channel": str(row.preferred_channel),
            "urban": bool(row.urban),
            "internet_access": bool(row.internet_access),
            "betweenness": float(row.betweenness),
            "eigenvector": float(row.eigenvector),
            "influence_score": float(row.influence_score),
            "hub_node": bool(row.hub_node),
        }
    nx.set_node_attributes(graph, attrs)


def _build_summary(
    graph: nx.Graph,
    merged_df: pd.DataFrame,
    config: Phase3NetworkConfig,
    calibration: MoldovaCalibration,
) -> dict[str, Any]:
    degrees = np.array([float(d) for _, d in graph.degree()], dtype=float)
    channel_counts = merged_df["preferred_channel"].value_counts(normalize=True).to_dict()

    hub_nodes = merged_df[merged_df["hub_node"]]["node_id"].astype(int).tolist()
    hub_degree_sum = float(sum(dict(graph.degree(hub_nodes)).values())) if hub_nodes else 0.0
    total_degree = float(np.sum(degrees)) if len(degrees) else 1.0

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": asdict(config),
        "calibration": asdict(calibration),
        "graph": {
            "nodes": int(graph.number_of_nodes()),
            "edges": int(graph.number_of_edges()),
            "density": float(nx.density(graph)),
            "average_degree": float(np.mean(degrees)),
            "degree_std": float(np.std(degrees)),
            "degree_gini": _gini(degrees),
            "average_clustering": float(nx.average_clustering(graph)),
            "is_connected": bool(nx.is_connected(graph)),
            "hub_nodes": len(hub_nodes),
            "hub_degree_share": hub_degree_sum / total_degree,
        },
        "agent_profiles": {
            "age_mean": float(merged_df["age"].mean()),
            "age_std": float(merged_df["age"].std(ddof=0)),
            "critical_thinking_mean": float(merged_df["critical_thinking"].mean()),
            "media_trust_mean": float(merged_df["media_trust"].mean()),
            "internet_access_share": float(merged_df["internet_access"].mean()),
            "urban_share": float(merged_df["urban"].mean()),
            "preferred_channel_share": {k: float(v) for k, v in channel_counts.items()},
        },
        "sources": [asdict(src) for src in SOURCES],
    }


def _build_mesa_payload(
    graph: nx.Graph,
    merged_df: pd.DataFrame,
    summary: dict[str, Any],
) -> dict[str, Any]:
    nodes = []
    for row in merged_df.itertuples(index=False):
        nodes.append(
            {
                "id": int(row.node_id),
                "initial_state": "S",
                "age": int(row.age),
                "critical_thinking": float(row.critical_thinking),
                "media_trust": float(row.media_trust),
                "preferred_channel": str(row.preferred_channel),
                "urban": bool(row.urban),
                "internet_access": bool(row.internet_access),
                "betweenness": float(row.betweenness),
                "eigenvector": float(row.eigenvector),
                "influence_score": float(row.influence_score),
                "hub_node": bool(row.hub_node),
            }
        )

    edges = [{"source": int(u), "target": int(v)} for u, v in graph.edges()]
    adjacency = {str(int(n)): [int(nb) for nb in graph.neighbors(n)] for n in graph.nodes()}
    hub_nodes = [n["id"] for n in nodes if n["hub_node"]]

    return {
        "metadata": {
            "phase": 3,
            "model": "SEIZ-ready synthetic Moldova network",
            "generated_at_utc": summary["generated_at_utc"],
            "node_count": summary["graph"]["nodes"],
            "edge_count": summary["graph"]["edges"],
        },
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "hub_nodes": hub_nodes,
    }


def export_artifacts(
    graph: nx.Graph,
    merged_df: pd.DataFrame,
    summary: dict[str, Any],
    config: Phase3NetworkConfig,
) -> Phase3Artifacts:
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    graphml_path = output_dir / "moldova_network.graphml"
    adjacency_path = output_dir / "adjacency_matrix.csv.gz"
    agents_csv_path = output_dir / "agent_profiles.csv"
    agents_json_path = output_dir / "agent_profiles.json"
    edges_csv_path = output_dir / "edge_list.csv"
    mesa_payload_path = output_dir / "mesa_payload_phase3.json"
    summary_path = output_dir / "network_summary.json"

    nx.write_graphml(graph, graphml_path)

    adjacency_df = nx.to_pandas_adjacency(graph, dtype=int)
    adjacency_df.to_csv(adjacency_path, compression="gzip")

    merged_df.sort_values("node_id").to_csv(agents_csv_path, index=False)
    agents_json_path.write_text(
        json.dumps(merged_df.sort_values("node_id").to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )

    nx.to_pandas_edgelist(graph).to_csv(edges_csv_path, index=False)

    mesa_payload = _build_mesa_payload(graph, merged_df, summary)
    mesa_payload_path.write_text(json.dumps(mesa_payload, indent=2), encoding="utf-8")

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return Phase3Artifacts(
        output_dir=output_dir,
        graphml_path=graphml_path,
        adjacency_path=adjacency_path,
        agents_csv_path=agents_csv_path,
        agents_json_path=agents_json_path,
        edges_csv_path=edges_csv_path,
        mesa_payload_path=mesa_payload_path,
        summary_path=summary_path,
    )


def build_phase3_network(config: Phase3NetworkConfig) -> Phase3Artifacts:
    calibration = default_calibration()

    graph = build_scale_free_graph(config)
    profiles_df = build_agent_profiles(graph, calibration, seed=config.seed)
    metrics_df = compute_centrality_metrics(graph, config)
    metrics_tagged_df = tag_hubs(metrics_df, hub_top_fraction=config.hub_top_fraction)

    merged_df = profiles_df.merge(metrics_tagged_df, on="node_id", how="inner")
    _attach_node_attributes(graph, merged_df)

    summary = _build_summary(graph, merged_df, config, calibration)
    return export_artifacts(graph, merged_df, summary, config)
