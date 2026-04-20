from __future__ import annotations

from runtime_bootstrap import patch_windows_platform

patch_windows_platform()

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

STATE_S = 0
STATE_E = 1
STATE_I = 2
STATE_Z = 3

STATE_NAMES = {
    STATE_S: "S",
    STATE_E: "E",
    STATE_I: "I",
    STATE_Z: "Z",
}

SENSATIONAL_KEYWORDS = (
    "breaking",
    "urgent",
    "shocking",
    "scandal",
    "crisis",
    "fals",
    "fake",
    "propaganda",
    "exclusive",
    "alert",
    "panic",
    "truth",
    "bombshell",
)


@dataclass
class SimulationConfig:
    num_agents: int = 1000
    attach_edges: int = 3
    ticks: int = 80
    runs: int = 10
    initial_infected: int = 8
    hub_percent: float = 0.05
    random_seed: int = 42


def load_phase3_network_payload(
    payload_path: Path,
) -> Tuple[nx.Graph, pd.DataFrame, Set[int]]:
    with Path(payload_path).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    nodes_payload = payload.get("nodes")
    edges_payload = payload.get("edges")
    if not isinstance(nodes_payload, list) or not isinstance(edges_payload, list):
        raise ValueError(
            "Phase 3 payload is missing 'nodes' or 'edges' arrays.",
        )

    graph = nx.Graph()
    records: List[Dict[str, Any]] = []
    hub_nodes: Set[int] = set()

    for node_raw in nodes_payload:
        if not isinstance(node_raw, dict):
            continue

        node_id = int(_safe_float(node_raw.get("id"), -1))
        if node_id < 0:
            continue

        critical_thinking = float(np.clip(_safe_float(node_raw.get("critical_thinking"), 0.5), 0.0, 1.0))
        media_trust = float(np.clip(_safe_float(node_raw.get("media_trust"), 0.5), 0.0, 1.0))
        preferred_channel = str(node_raw.get("preferred_channel") or "Social")

        if preferred_channel not in {"Mouth", "Social", "TV"}:
            preferred_channel = "Social"

        betweenness = max(0.0, _safe_float(node_raw.get("betweenness"), 0.0))
        eigenvector = max(0.0, _safe_float(node_raw.get("eigenvector"), 0.0))
        influence_score = max(
            0.0,
            _safe_float(
                node_raw.get("influence_score"),
                0.5 * betweenness + 0.5 * eigenvector,
            ),
        )
        is_hub = bool(node_raw.get("hub_node", False))

        graph.add_node(node_id)
        records.append(
            {
                "node_id": node_id,
                "age": int(_safe_float(node_raw.get("age"), 40.0)),
                "critical_thinking": critical_thinking,
                "media_trust": media_trust,
                "preferred_channel": preferred_channel,
                "betweenness": betweenness,
                "eigenvector": eigenvector,
                "hub_score": influence_score,
                "is_hub": is_hub,
            }
        )

        if is_hub:
            hub_nodes.add(node_id)

    for edge_raw in edges_payload:
        if not isinstance(edge_raw, dict):
            continue

        source = int(_safe_float(edge_raw.get("source"), -1))
        target = int(_safe_float(edge_raw.get("target"), -1))
        if source < 0 or target < 0:
            continue
        if source == target:
            continue

        graph.add_edge(source, target)

    agents = pd.DataFrame(records)
    if agents.empty:
        raise ValueError("Phase 3 payload produced no valid agent rows.")

    # Keep ordering stable and aligned to node ids 0..N-1 expected by the simulator.
    agents = agents.sort_values("node_id").reset_index(drop=True)
    expected_ids = np.arange(len(agents), dtype=int)
    node_ids = agents["node_id"].to_numpy(dtype=int)
    if not np.array_equal(node_ids, expected_ids):
        raise ValueError(
            "Phase 3 payload node ids must be contiguous [0..N-1] for simulation indexing.",
        )

    if not hub_nodes:
        hub_mask = agents["is_hub"].to_numpy(dtype=bool)
        hub_nodes = set(agents.loc[hub_mask, "node_id"].astype(int).tolist())

    return graph, agents, hub_nodes


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float, np.number)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _load_json_records(path: Path) -> List[Dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [row for row in payload if isinstance(row, dict)]


def _normalize_metrics(raw: Dict[str, Any]) -> Dict[str, float]:
    shares = _safe_float(raw.get("shares", raw.get("forwards_or_shares", 0.0)))
    likes = _safe_float(raw.get("likes", 0.0))

    reactions = raw.get("reactions")
    if isinstance(reactions, dict):
        reaction_sum = float(sum(_safe_float(v) for v in reactions.values()))
        likes = max(likes, reaction_sum)

    return {
        "views": _safe_float(raw.get("views", 0.0)),
        "likes": likes,
        "shares": shares,
        "comments": _safe_float(raw.get("comments", 0.0)),
    }


def _normalize_record(raw: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    metrics_raw = raw.get("engagement_metrics")
    if not isinstance(metrics_raw, dict):
        metrics_raw = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}

    metrics = _normalize_metrics(metrics_raw)
    top_comments = _safe_list(raw.get("top_comments"))

    headline = str(raw.get("headline", "") or "").strip()
    body_text = str(raw.get("body_text", "") or "").strip()
    combined_text = f"{headline} {body_text}".strip()

    source = str(raw.get("source") or raw.get("source_domain") or "unknown")

    return {
        "article_id": str(raw.get("article_id") or ""),
        "source": source,
        "source_type": source_type,
        "is_fake": bool(raw.get("is_fake", False)),
        "publication_date": raw.get("publication_date"),
        "headline": headline,
        "body_text": body_text,
        "combined_text": combined_text,
        "views": metrics["views"],
        "likes": metrics["likes"],
        "shares": metrics["shares"],
        "comments": metrics["comments"],
        "top_comments": top_comments,
        "top_comment_count": float(len(top_comments)),
        "has_debunk_context": 1.0 if raw.get("debunk_context") else 0.0,
        "inferred_sources_count": float(len(_safe_list(raw.get("inferred_sources")))),
    }


def load_and_normalize_datasets(
    fake_path: Path,
    real_path: Path,
    telegram_path: Path,
) -> pd.DataFrame:
    datasets = [
        (Path(fake_path), "fake"),
        (Path(real_path), "real"),
        (Path(telegram_path), "telegram"),
    ]

    records: List[Dict[str, Any]] = []
    for path, source_type in datasets:
        for raw in _load_json_records(path):
            records.append(_normalize_record(raw, source_type))

    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No valid records found in provided datasets.")

    frame["views"] = frame["views"].clip(lower=0)
    frame["likes"] = frame["likes"].clip(lower=0)
    frame["shares"] = frame["shares"].clip(lower=0)
    frame["comments"] = frame["comments"].clip(lower=0)

    return frame


def _infer_source_type_from_phase2(raw: Dict[str, Any]) -> str:
    source = str(raw.get("source") or raw.get("source_domain") or "").lower()

    if "telegram" in source:
        return "telegram"
    if source in {"stiri.md", "protv", "jurnal.md", "protv.md"}:
        return "real"
    if bool(raw.get("is_fake", False)):
        return "fake"
    return "real"


def load_phase2_normalized_dataset(phase2_path: Path) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []

    for raw in _load_json_records(phase2_path):
        metrics = _normalize_metrics(
            raw.get("engagement_metrics")
            if isinstance(raw.get("engagement_metrics"), dict)
            else raw.get("metrics")
            if isinstance(raw.get("metrics"), dict)
            else {}
        )
        sentiment = raw.get("sentiment") if isinstance(raw.get("sentiment"), dict) else {}
        headline = str(raw.get("headline", "") or "").strip()
        body_text = str(raw.get("body_text", "") or "").strip()
        text_en = str(raw.get("text_en", "") or "").strip()
        impact_score = float(
            np.clip(
                _safe_float(raw.get("impact_score"), _safe_float(sentiment.get("emotional_score"), 0.0)),
                -1.0,
                1.0,
            )
        )
        emotional_intensity = float(
            np.clip(
                _safe_float(sentiment.get("emotional_intensity"), abs(impact_score)),
                0.0,
                1.0,
            )
        )
        source_type = _infer_source_type_from_phase2(raw)

        records.append(
            {
                "article_id": str(raw.get("article_id") or ""),
                "source": str(raw.get("source") or raw.get("source_domain") or "unknown"),
                "source_type": source_type,
                "is_fake": bool(raw.get("is_fake", False)),
                "publication_date": raw.get("publication_date"),
                "headline": headline,
                "body_text": body_text,
                "combined_text": text_en or f"{headline} {body_text}".strip(),
                "views": metrics["views"],
                "likes": metrics["likes"],
                "shares": metrics["shares"],
                "comments": metrics["comments"],
                "top_comments": _safe_list(raw.get("top_comments")),
                "top_comment_count": float(len(_safe_list(raw.get("top_comments")))),
                "has_debunk_context": 1.0 if raw.get("debunk_context") else 0.0,
                "inferred_sources_count": float(len(_safe_list(raw.get("inferred_sources")))),
                "engagement_total": _safe_float(raw.get("engagement_total"), 0.0),
                "impact_score": impact_score,
                "phase2_emotional_intensity": emotional_intensity,
                "phase2_language": str(raw.get("language_detected") or "unknown"),
                "phase2_reference_bin": str(raw.get("reference_bin") or ""),
                "phase2_translation_applied": bool(raw.get("translation_applied", False)),
                "feature_source": "phase2_normalized",
            }
        )

    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError(f"No valid Phase 2 records found in {phase2_path}.")

    frame["views"] = frame["views"].clip(lower=0)
    frame["likes"] = frame["likes"].clip(lower=0)
    frame["shares"] = frame["shares"].clip(lower=0)
    frame["comments"] = frame["comments"].clip(lower=0)
    frame["engagement_total"] = frame["engagement_total"].clip(lower=0)
    return frame


def _estimate_emotional_intensity(text: str, headline: str) -> float:
    safe_text = (text or "").strip()
    safe_headline = (headline or "").strip()
    full = f"{safe_headline} {safe_text}".lower()

    exclamation_score = min(full.count("!"), 8) / 8.0
    question_score = min(full.count("?"), 6) / 6.0
    uppercase_ratio = 0.0
    if safe_headline:
        uppercase_ratio = sum(1 for c in safe_headline if c.isupper()) / max(len(safe_headline), 1)

    keyword_hits = sum(1 for keyword in SENSATIONAL_KEYWORDS if keyword in full)
    keyword_score = min(keyword_hits, 6) / 6.0
    length_score = min(len(full) / 1500.0, 1.0)

    score = (
        0.35 * exclamation_score
        + 0.10 * question_score
        + 0.20 * uppercase_ratio
        + 0.25 * keyword_score
        + 0.10 * length_score
    )
    return float(np.clip(score, 0.0, 1.0))


def _infer_seed_channel(source_type: str, source: str) -> str:
    src = (source or "").lower()
    if source_type == "telegram":
        return "Social"
    if source_type == "real" or src in {"stiri.md", "protv", "jurnal.md"}:
        return "TV"
    if source_type == "fake":
        return "Social"
    return "Mouth"


def compute_news_features(news_df: pd.DataFrame) -> pd.DataFrame:
    frame = news_df.copy()

    views = frame["views"].to_numpy(dtype=float)
    likes = frame["likes"].to_numpy(dtype=float)
    shares = frame["shares"].to_numpy(dtype=float)
    comments = frame["comments"].to_numpy(dtype=float)
    top_comment_count = frame["top_comment_count"].to_numpy(dtype=float)

    adjusted_views = np.maximum(views, 1.0)
    comment_density = comments / np.sqrt(adjusted_views)
    share_velocity = shares / np.sqrt(adjusted_views)
    comment_vs_like = comments / np.maximum(likes + 1.0, 1.0)
    engagement_total = frame.get("engagement_total")
    if engagement_total is None:
        engagement_total_values = views + likes + shares + comments
    else:
        engagement_total_values = np.maximum(frame["engagement_total"].to_numpy(dtype=float), 0.0)
    engagement_signal = np.log1p(engagement_total_values)

    impact_magnitude = np.abs(
        np.clip(
            frame["impact_score"].to_numpy(dtype=float),
            -1.0,
            1.0,
        )
    ) if "impact_score" in frame.columns else None

    raw_controversy = (
        0.35 * comment_density
        + 0.30 * share_velocity
        + 0.20 * comment_vs_like
        + 0.15 * (top_comment_count / np.maximum(top_comment_count + 3.0, 1.0))
    ) + 0.12 * frame["has_debunk_context"].to_numpy(dtype=float) + 0.08 * engagement_signal

    if impact_magnitude is not None:
        raw_controversy = raw_controversy + 0.18 * impact_magnitude

    if "phase2_emotional_intensity" in frame.columns:
        raw_emotional = np.clip(frame["phase2_emotional_intensity"].to_numpy(dtype=float), 0.0, 1.0)
        frame["feature_source"] = "phase2_normalized"
    else:
        raw_emotional = np.array(
            [
                _estimate_emotional_intensity(text=combined, headline=headline)
                for combined, headline in zip(frame["combined_text"], frame["headline"])
            ],
            dtype=float,
        )
        frame["feature_source"] = frame.get("feature_source", "raw_heuristic")

    raw_matrix = np.column_stack([raw_controversy, raw_emotional])
    scaler = MinMaxScaler(feature_range=(0.0, 1.0))
    scaled = scaler.fit_transform(raw_matrix)

    frame["controversy_score"] = scaled[:, 0]
    if "phase2_emotional_intensity" in frame.columns:
        frame["emotional_intensity"] = raw_emotional
    else:
        frame["emotional_intensity"] = scaled[:, 1]

    if "impact_score" not in frame.columns:
        frame["impact_score"] = np.where(
            frame["is_fake"].to_numpy(dtype=bool),
            frame["emotional_intensity"],
            -0.5 * frame["emotional_intensity"],
        )

    if impact_magnitude is None:
        impact_magnitude = np.abs(np.clip(frame["impact_score"].to_numpy(dtype=float), -1.0, 1.0))

    transmission_base = 0.08 + 0.72 * (
        0.50 * frame["controversy_score"] + 0.30 * frame["emotional_intensity"] + 0.20 * impact_magnitude
    )
    fake_bonus = np.where(frame["is_fake"].to_numpy(dtype=bool), 0.04, -0.02)

    frame["transmission_probability"] = np.clip(transmission_base + fake_bonus, 0.03, 0.95)
    frame["seed_channel"] = [
        _infer_seed_channel(source_type=source_type, source=source)
        for source_type, source in zip(frame["source_type"], frame["source"])
    ]

    return frame


def build_population_graph(
    config: SimulationConfig,
    rng: np.random.Generator,
) -> Tuple[nx.Graph, pd.DataFrame, Set[int]]:
    graph_seed = int(rng.integers(0, 2**31 - 1))
    graph = nx.barabasi_albert_graph(
        n=config.num_agents,
        m=config.attach_edges,
        seed=graph_seed,
    )

    node_count = graph.number_of_nodes()
    node_ids = np.arange(node_count, dtype=int)

    ages = rng.integers(18, 81, size=node_count)
    critical_thinking = np.clip(rng.beta(4.0, 3.5, size=node_count), 0.0, 1.0)
    media_trust = np.clip(rng.beta(3.2, 3.0, size=node_count), 0.0, 1.0)

    preferred_channel = rng.choice(
        np.array(["Mouth", "Social", "TV"]),
        size=node_count,
        replace=True,
        p=np.array([0.26, 0.54, 0.20]),
    )

    sample_k = min(max(30, node_count // 4), 250)
    centrality_seed = int(rng.integers(0, 2**31 - 1))
    betweenness = nx.betweenness_centrality(graph, k=sample_k, seed=centrality_seed, normalized=True)

    try:
        eigen = nx.eigenvector_centrality(graph, max_iter=500, tol=1.0e-6)
    except nx.NetworkXException:
        eigen = {node: 0.0 for node in graph.nodes()}

    bet_values = np.array([float(betweenness[node]) for node in node_ids], dtype=float)
    eig_values = np.array([float(eigen[node]) for node in node_ids], dtype=float)

    hub_score = 0.5 * bet_values + 0.5 * eig_values
    hub_count = max(1, int(round(config.hub_percent * node_count)))
    ranked_indices = np.argsort(hub_score)[::-1]
    hub_nodes = {int(node_ids[idx]) for idx in ranked_indices[:hub_count]}

    agents = pd.DataFrame(
        {
            "node_id": node_ids,
            "age": ages,
            "critical_thinking": critical_thinking,
            "media_trust": media_trust,
            "preferred_channel": preferred_channel,
            "betweenness": bet_values,
            "eigenvector": eig_values,
            "hub_score": hub_score,
            "is_hub": [node in hub_nodes for node in node_ids],
        }
    )

    return graph, agents, hub_nodes


def _state_counts(state: np.ndarray) -> Dict[str, int]:
    return {
        "S": int(np.sum(state == STATE_S)),
        "E": int(np.sum(state == STATE_E)),
        "I": int(np.sum(state == STATE_I)),
        "Z": int(np.sum(state == STATE_Z)),
    }


def _distort_parameter(value: float, rng: np.random.Generator) -> float:
    return float(np.clip(value * (1.0 + rng.uniform(-0.01, 0.01)), 0.01, 0.99))


def run_single_simulation(
    graph: nx.Graph,
    agents: pd.DataFrame,
    news_item: Dict[str, Any],
    config: SimulationConfig,
    rng: np.random.Generator,
    prebunk_hubs: bool,
    hub_nodes: Optional[Set[int]] = None,
) -> Tuple[pd.DataFrame, np.ndarray]:
    n = graph.number_of_nodes()
    state = np.full(n, STATE_S, dtype=np.int8)
    exposed_age = np.full(n, -1, dtype=np.int8)

    if prebunk_hubs and hub_nodes:
        hub_idx = np.array(sorted(hub_nodes), dtype=int)
        state[hub_idx] = STATE_Z

    susceptible = np.where(state == STATE_S)[0]
    if len(susceptible) == 0:
        raise ValueError("No susceptible nodes available for initial infection.")

    initial_seed_count = min(config.initial_infected, len(susceptible))
    initial_infected = rng.choice(susceptible, size=initial_seed_count, replace=False)
    state[initial_infected] = STATE_I

    neighbors: List[np.ndarray] = [
        np.fromiter(graph.neighbors(node), dtype=int)
        for node in range(n)
    ]

    critical = agents["critical_thinking"].to_numpy(dtype=float)
    media_trust = agents["media_trust"].to_numpy(dtype=float)
    preferred = agents["preferred_channel"].to_numpy()

    beta = float(news_item["transmission_probability"])
    emotional = float(news_item["emotional_intensity"])
    controversy = float(news_item["controversy_score"])
    seed_channel = str(news_item["seed_channel"])

    rows: List[Dict[str, Any]] = []
    counts = _state_counts(state)
    rows.append(
        {
            "tick": 0,
            "S": counts["S"],
            "E": counts["E"],
            "I": counts["I"],
            "Z": counts["Z"],
            "beta": beta,
            "emotional_intensity": emotional,
            "controversy_score": controversy,
        }
    )

    for tick in range(1, config.ticks + 1):
        matured = np.where((state == STATE_E) & (exposed_age >= 1))[0]
        for node in matured:
            belief = (
                0.48 * emotional
                + 0.28 * controversy
                + 0.24 * media_trust[node]
                - 0.42 * critical[node]
            )
            infect_prob = float(np.clip(0.08 + beta * (0.55 + belief), 0.02, 0.98))
            if rng.random() < infect_prob:
                state[node] = STATE_I
            else:
                state[node] = STATE_Z
            exposed_age[node] = -1

        infected_nodes = np.where(state == STATE_I)[0]
        newly_exposed: Set[int] = set()
        share_events = 0

        for node in infected_nodes:
            direct_neighbors = neighbors[node]
            target_nodes: Set[int] = set(int(x) for x in direct_neighbors.tolist())

            channel = preferred[node]
            multiplier = 1.0
            if channel == "Social":
                multiplier *= 1.15
                second_hop: List[int] = []
                for nb in direct_neighbors[: min(3, len(direct_neighbors))]:
                    second_hop.extend(int(x) for x in neighbors[int(nb)].tolist())
                if second_hop:
                    sampled_second_hop = rng.choice(
                        np.array(second_hop, dtype=int),
                        size=min(4, len(second_hop)),
                        replace=False,
                    )
                    target_nodes.update(int(x) for x in np.atleast_1d(sampled_second_hop))
            elif channel == "TV":
                multiplier *= 1.05
                susceptible_pool = np.where(state == STATE_S)[0]
                if len(susceptible_pool) > 0:
                    broadcast_count = min(len(susceptible_pool), max(1, int(1 + controversy * 4)))
                    broadcast_targets = rng.choice(
                        susceptible_pool,
                        size=broadcast_count,
                        replace=False,
                    )
                    target_nodes.update(int(x) for x in np.atleast_1d(broadcast_targets))

            if seed_channel == channel:
                multiplier *= 1.12

            for target in target_nodes:
                if target < 0 or target >= n:
                    continue
                if state[target] != STATE_S:
                    continue

                resistance = 0.55 * critical[target] + 0.25 * (1.0 - media_trust[target])
                exposure_prob = float(np.clip(beta * multiplier * (1.0 - resistance), 0.0, 0.95))

                if rng.random() < exposure_prob:
                    newly_exposed.add(target)
                    share_events += 1

        spillover_hits = int(round(controversy * 3.0))
        if spillover_hits > 0:
            susceptible_pool = np.where(state == STATE_S)[0]
            if len(susceptible_pool) > 0:
                spillover_count = min(len(susceptible_pool), spillover_hits)
                spillover_targets = rng.choice(
                    susceptible_pool,
                    size=spillover_count,
                    replace=False,
                )
                newly_exposed.update(int(x) for x in np.atleast_1d(spillover_targets))

        for node in newly_exposed:
            if state[node] == STATE_S:
                state[node] = STATE_E
                exposed_age[node] = 0

        for _ in range(share_events):
            beta = _distort_parameter(beta, rng)
            emotional = _distort_parameter(emotional, rng)
            controversy = _distort_parameter(controversy, rng)

        exposed_mask = (state == STATE_E) & (exposed_age >= 0)
        exposed_age[exposed_mask] += 1

        counts = _state_counts(state)
        rows.append(
            {
                "tick": tick,
                "S": counts["S"],
                "E": counts["E"],
                "I": counts["I"],
                "Z": counts["Z"],
                "beta": beta,
                "emotional_intensity": emotional,
                "controversy_score": controversy,
            }
        )

        if counts["I"] == 0 and counts["E"] == 0:
            for late_tick in range(tick + 1, config.ticks + 1):
                rows.append(
                    {
                        "tick": late_tick,
                        "S": counts["S"],
                        "E": counts["E"],
                        "I": counts["I"],
                        "Z": counts["Z"],
                        "beta": beta,
                        "emotional_intensity": emotional,
                        "controversy_score": controversy,
                    }
                )
            break

    return pd.DataFrame(rows), state


def _extract_scenario_metrics(avg_timeline: pd.DataFrame, scenario: str) -> Dict[str, float]:
    scenario_df = avg_timeline[avg_timeline["scenario"] == scenario].sort_values("tick")
    infected = scenario_df["I"].to_numpy(dtype=float)
    ticks = scenario_df["tick"].to_numpy(dtype=float)

    peak_idx = int(np.argmax(infected)) if len(infected) else 0
    peak_val = float(infected[peak_idx]) if len(infected) else 0.0
    peak_tick = int(ticks[peak_idx]) if len(ticks) else 0
    auc = float(np.trapezoid(infected, ticks)) if len(ticks) > 1 else 0.0

    return {
        "peak_infected": peak_val,
        "tick_of_peak": peak_tick,
        "infected_auc": auc,
        "final_infected": float(infected[-1]) if len(infected) else 0.0,
    }


def _bootstrap_mean_interval(
    values: List[float],
    rng: np.random.Generator,
    n_boot: int = 2000,
) -> Dict[str, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}
    if array.size == 1:
        only = float(array[0])
        return {"mean": only, "ci_low": only, "ci_high": only, "n": 1}

    boot = np.empty(n_boot, dtype=float)
    for idx in range(n_boot):
        sample = rng.choice(array, size=array.size, replace=True)
        boot[idx] = float(np.mean(sample))

    return {
        "mean": float(np.mean(array)),
        "ci_low": float(np.quantile(boot, 0.025)),
        "ci_high": float(np.quantile(boot, 0.975)),
        "n": int(array.size),
    }


def _summarize_run_metric_intervals(
    metrics_df: pd.DataFrame,
    seed: int,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    summary: Dict[str, Dict[str, Dict[str, float]]] = {}
    metric_names = ["peak_infected", "tick_of_peak", "infected_auc", "final_infected"]

    for scenario in sorted(metrics_df["scenario"].unique().tolist()):
        scenario_df = metrics_df[metrics_df["scenario"] == scenario]
        scenario_rng = np.random.default_rng(seed + len(summary) + 1)
        summary[scenario] = {}
        for metric_name in metric_names:
            values = scenario_df[metric_name].astype(float).tolist()
            summary[scenario][metric_name] = _bootstrap_mean_interval(values, rng=scenario_rng)

    return summary


def _summarize_paired_run_deltas(
    metrics_df: pd.DataFrame,
    seed: int,
) -> Dict[str, Dict[str, float]]:
    pivot = metrics_df.pivot(index="run", columns="scenario")
    if not isinstance(pivot.columns, pd.MultiIndex):
        return {}

    scenario_labels = set(pivot.columns.get_level_values(-1).tolist())
    if "baseline" not in scenario_labels or "prebunk_hubs" not in scenario_labels:
        return {}

    baseline_cols = pivot.xs("baseline", axis=1, level="scenario")
    prebunk_cols = pivot.xs("prebunk_hubs", axis=1, level="scenario")

    paired = pd.DataFrame(
        {
            "peak_infected_delta": baseline_cols["peak_infected"] - prebunk_cols["peak_infected"],
            "infected_auc_delta": baseline_cols["infected_auc"] - prebunk_cols["infected_auc"],
            "final_infected_delta": baseline_cols["final_infected"] - prebunk_cols["final_infected"],
            "tick_of_peak_delay": prebunk_cols["tick_of_peak"] - baseline_cols["tick_of_peak"],
        }
    ).dropna()

    if paired.empty:
        return {}

    rng = np.random.default_rng(seed + 10_000)
    summary: Dict[str, Dict[str, float]] = {}

    for metric_name in paired.columns.tolist():
        values = paired[metric_name].astype(float).tolist()
        interval = _bootstrap_mean_interval(values, rng=rng)
        positive_probability = float(np.mean(np.asarray(values, dtype=float) > 0.0))
        non_negative_probability = float(np.mean(np.asarray(values, dtype=float) >= 0.0))
        summary[metric_name] = {
            **interval,
            "positive_share": positive_probability,
            "non_negative_share": non_negative_probability,
        }

    return summary


def run_phase45_pipeline(
    news_df: pd.DataFrame,
    config: SimulationConfig,
    phase3_payload_path: Optional[Path] = None,
) -> Dict[str, Any]:
    rng = np.random.default_rng(config.random_seed)

    fake_candidates = news_df[news_df["is_fake"] == True]  # noqa: E712
    candidate_pool = fake_candidates if not fake_candidates.empty else news_df
    chosen_news = (
        candidate_pool.sort_values("transmission_probability", ascending=False)
        .head(1)
        .iloc[0]
        .to_dict()
    )

    all_runs: List[pd.DataFrame] = []
    hub_rows: List[Dict[str, Any]] = []
    snapshot_graph: Optional[nx.Graph] = None
    snapshot_state: Optional[np.ndarray] = None

    payload_graph: Optional[nx.Graph] = None
    payload_agents: Optional[pd.DataFrame] = None
    payload_hubs: Optional[Set[int]] = None
    network_source = "synthetic"
    if phase3_payload_path is not None:
        payload_graph, payload_agents, payload_hubs = load_phase3_network_payload(phase3_payload_path)
        network_source = "phase3_payload"

    for run_id in range(1, config.runs + 1):
        run_rng = np.random.default_rng(int(rng.integers(0, 2**31 - 1)))
        if payload_graph is not None and payload_agents is not None and payload_hubs is not None:
            graph, agents, hub_nodes = payload_graph, payload_agents, payload_hubs
        else:
            graph, agents, hub_nodes = build_population_graph(config=config, rng=run_rng)

        base_rng = np.random.default_rng(int(run_rng.integers(0, 2**31 - 1)))
        baseline_timeline, baseline_state = run_single_simulation(
            graph=graph,
            agents=agents,
            news_item=chosen_news,
            config=config,
            rng=base_rng,
            prebunk_hubs=False,
            hub_nodes=hub_nodes,
        )
        baseline_timeline["scenario"] = "baseline"
        baseline_timeline["run"] = run_id
        all_runs.append(baseline_timeline)

        intervention_rng = np.random.default_rng(int(run_rng.integers(0, 2**31 - 1)))
        intervention_timeline, _ = run_single_simulation(
            graph=graph,
            agents=agents,
            news_item=chosen_news,
            config=config,
            rng=intervention_rng,
            prebunk_hubs=True,
            hub_nodes=hub_nodes,
        )
        intervention_timeline["scenario"] = "prebunk_hubs"
        intervention_timeline["run"] = run_id
        all_runs.append(intervention_timeline)

        for hub in sorted(hub_nodes):
            hub_rows.append({"run": run_id, "node_id": int(hub)})

        if run_id == 1:
            snapshot_graph = graph.copy()
            snapshot_state = baseline_state.copy()

    timeline = pd.concat(all_runs, ignore_index=True)
    run_metrics_rows: List[Dict[str, Any]] = []
    for (scenario, run_id), run_df in timeline.groupby(["scenario", "run"]):
        metrics = _extract_scenario_metrics(run_df, scenario=str(scenario))
        run_metrics_rows.append(
            {
                "scenario": str(scenario),
                "run": int(run_id),
                **metrics,
            }
        )
    run_metrics = pd.DataFrame(run_metrics_rows).sort_values(["scenario", "run"]).reset_index(drop=True)

    avg_timeline = (
        timeline.groupby(["scenario", "tick"], as_index=False)
        [["S", "E", "I", "Z", "beta", "emotional_intensity", "controversy_score"]]
        .mean()
    )

    baseline_metrics = _extract_scenario_metrics(avg_timeline, "baseline")
    prebunk_metrics = _extract_scenario_metrics(avg_timeline, "prebunk_hubs")
    run_metric_intervals = _summarize_run_metric_intervals(run_metrics, seed=config.random_seed)
    paired_run_deltas = _summarize_paired_run_deltas(run_metrics, seed=config.random_seed)

    reduction_peak = 0.0
    if baseline_metrics["peak_infected"] > 0:
        reduction_peak = 100.0 * (
            baseline_metrics["peak_infected"] - prebunk_metrics["peak_infected"]
        ) / baseline_metrics["peak_infected"]

    reduction_auc = 0.0
    if baseline_metrics["infected_auc"] > 0:
        reduction_auc = 100.0 * (
            baseline_metrics["infected_auc"] - prebunk_metrics["infected_auc"]
        ) / baseline_metrics["infected_auc"]

    summary = {
        "selected_news_article_id": chosen_news.get("article_id", ""),
        "selected_news_source": chosen_news.get("source", ""),
        "selected_news_fake_label": bool(chosen_news.get("is_fake", False)),
        "selected_news_channel": chosen_news.get("seed_channel", ""),
        "selected_news_feature_source": chosen_news.get("feature_source", "unknown"),
        "selected_news_metrics": {
            "controversy_score": float(chosen_news.get("controversy_score", 0.0)),
            "emotional_intensity": float(chosen_news.get("emotional_intensity", 0.0)),
            "impact_score": float(chosen_news.get("impact_score", 0.0)),
            "transmission_probability": float(chosen_news.get("transmission_probability", 0.0)),
        },
        "baseline": baseline_metrics,
        "prebunk_hubs": prebunk_metrics,
        "reduction": {
            "peak_infected_percent": float(reduction_peak),
            "infected_auc_percent": float(reduction_auc),
        },
        "run_metric_intervals": run_metric_intervals,
        "paired_run_deltas": paired_run_deltas,
        "simulation_config": {
            "num_agents": int(snapshot_graph.number_of_nodes()) if snapshot_graph is not None else config.num_agents,
            "attach_edges": config.attach_edges,
            "ticks": config.ticks,
            "runs": config.runs,
            "initial_infected": config.initial_infected,
            "hub_percent": config.hub_percent,
            "random_seed": config.random_seed,
            "network_source": network_source,
            "phase3_payload_path": str(phase3_payload_path) if phase3_payload_path is not None else None,
        },
    }

    return {
        "selected_news": chosen_news,
        "timeline": timeline,
        "run_metrics": run_metrics,
        "average_timeline": avg_timeline,
        "hub_nodes": pd.DataFrame(hub_rows),
        "summary": summary,
        "snapshot_graph": snapshot_graph,
        "snapshot_state": snapshot_state,
    }


def plot_average_curves(avg_timeline: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = avg_timeline[avg_timeline["scenario"] == "baseline"].sort_values("tick")
    prebunk = avg_timeline[avg_timeline["scenario"] == "prebunk_hubs"].sort_values("tick")

    plt.figure(figsize=(10, 6))
    plt.plot(baseline["tick"], baseline["I"], label="Baseline I", linewidth=2.5, color="#c62828")
    plt.plot(prebunk["tick"], prebunk["I"], label="Prebunk Hubs I", linewidth=2.5, color="#2e7d32")
    plt.xlabel("Tick")
    plt.ylabel("Average Infected Nodes")
    plt.title("Infected Curve: Baseline vs Prebunking")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "infected_curve_comparison.png", dpi=160, bbox_inches="tight")
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for axis, scenario, title in [
        (axes[0], baseline, "Baseline State Trajectories"),
        (axes[1], prebunk, "Prebunk Hubs State Trajectories"),
    ]:
        axis.plot(scenario["tick"], scenario["S"], label="S", color="#1e88e5")
        axis.plot(scenario["tick"], scenario["E"], label="E", color="#f9a825")
        axis.plot(scenario["tick"], scenario["I"], label="I", color="#d32f2f")
        axis.plot(scenario["tick"], scenario["Z"], label="Z", color="#2e7d32")
        axis.set_title(title)
        axis.set_xlabel("Tick")
        axis.grid(alpha=0.2)

    axes[0].set_ylabel("Average Node Count")
    axes[1].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(output_dir / "state_trajectories.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_network_snapshot(
    graph: Optional[nx.Graph],
    state: Optional[np.ndarray],
    output_path: Path,
    random_seed: int,
) -> None:
    if graph is None or state is None:
        return

    rng = np.random.default_rng(random_seed)
    nodes = np.array(sorted(graph.nodes()), dtype=int)
    sample_size = min(220, len(nodes))
    sampled_nodes = rng.choice(nodes, size=sample_size, replace=False)
    subgraph = graph.subgraph(sampled_nodes).copy()

    color_map = {
        STATE_S: "#1e88e5",
        STATE_E: "#f9a825",
        STATE_I: "#d32f2f",
        STATE_Z: "#2e7d32",
    }

    node_colors = [color_map[int(state[node])] for node in subgraph.nodes()]
    layout = nx.spring_layout(subgraph, seed=random_seed)

    plt.figure(figsize=(9, 9))
    nx.draw_networkx_nodes(subgraph, layout, node_size=40, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(subgraph, layout, width=0.35, alpha=0.20)
    plt.title("Network Snapshot (sampled nodes)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close()
