from __future__ import annotations

import argparse
from pathlib import Path

from network import Phase3NetworkConfig, build_phase3_network


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 3: Build Moldova social network and calibrated agent profiles."
    )
    parser.add_argument("--nodes", type=int, default=1000, help="Number of graph nodes (default: 1000)")
    parser.add_argument("--m", type=int, default=3, help="Edges attached per new node in BA model")
    parser.add_argument("--seed", type=int, default=20260401, help="Random seed for reproducibility")
    parser.add_argument(
        "--hub-fraction",
        type=float,
        default=0.05,
        help="Top node fraction tagged as hubs (default: 0.05)",
    )
    parser.add_argument(
        "--betweenness-k",
        type=int,
        default=None,
        help="Optional sampled source count for approximate betweenness",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/phase3_network",
        help="Directory for generated files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = Phase3NetworkConfig(
        node_count=args.nodes,
        attach_edges_m=args.m,
        seed=args.seed,
        hub_top_fraction=args.hub_fraction,
        output_dir=args.output_dir,
        betweenness_k=args.betweenness_k,
    )

    artifacts = build_phase3_network(config)

    print("\nPhase 3 network build complete.")
    print(f"Output directory: {artifacts.output_dir}")
    print("Generated files:")
    print(f"- {Path(artifacts.graphml_path)}")
    print(f"- {Path(artifacts.adjacency_path)}")
    print(f"- {Path(artifacts.agents_csv_path)}")
    print(f"- {Path(artifacts.agents_json_path)}")
    print(f"- {Path(artifacts.edges_csv_path)}")
    print(f"- {Path(artifacts.mesa_payload_path)}")
    print(f"- {Path(artifacts.summary_path)}")


if __name__ == "__main__":
    main()
