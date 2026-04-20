from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from simulation.phase45 import (
        SimulationConfig,
        compute_news_features,
        load_and_normalize_datasets,
        load_phase2_normalized_dataset,
        plot_average_curves,
        run_phase45_pipeline,
        save_network_snapshot,
    )
except ModuleNotFoundError:
    import sys

    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from simulation.phase45 import (
        SimulationConfig,
        compute_news_features,
        load_and_normalize_datasets,
        load_phase2_normalized_dataset,
        plot_average_curves,
        run_phase45_pipeline,
        save_network_snapshot,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NewsProp Phase 4/5 simulation and analysis pipeline.",
    )

    parser.add_argument(
        "--phase2-normalized",
        type=Path,
        default=Path("phase2/outputs/normalized_with_phase2.json"),
        help="Optional Phase 2 normalized dataset JSON. Preferred when available.",
    )
    parser.add_argument(
        "--ignore-phase2-normalized",
        action="store_true",
        help="Force simulation to rebuild features from raw scraped datasets.",
    )
    parser.add_argument(
        "--fake",
        type=Path,
        default=Path("scraper/fake/stopfals_final_dataset.json"),
        help="Path to fake news dataset JSON.",
    )
    parser.add_argument(
        "--real",
        type=Path,
        default=Path("scraper/real/stirimd_dataset.json"),
        help="Path to real news dataset JSON.",
    )
    parser.add_argument(
        "--telegram",
        type=Path,
        default=Path("scraper/telegram/moldova_news_50.json"),
        help="Path to telegram dataset JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/phase45"),
        help="Directory where outputs are written.",
    )
    parser.add_argument(
        "--phase3-payload",
        type=Path,
        default=Path("outputs/phase3_network/mesa_payload_phase3.json"),
        help="Phase 3 Mesa payload JSON. If present, simulation runs on this fixed network.",
    )
    parser.add_argument(
        "--force-synthetic-network",
        action="store_true",
        help="Ignore Phase 3 payload and generate a synthetic BA graph each run.",
    )
    parser.add_argument("--num-agents", type=int, default=1000, help="Number of agents in the synthetic graph.")
    parser.add_argument("--attach-edges", type=int, default=3, help="Edges attached by each new node in BA graph.")
    parser.add_argument("--ticks", type=int, default=80, help="Simulation ticks per run.")
    parser.add_argument("--runs", type=int, default=10, help="Number of runs per scenario.")
    parser.add_argument("--initial-infected", type=int, default=8, help="Initial infected seeds.")
    parser.add_argument("--hub-percent", type=float, default=0.05, help="Top hub ratio to prebunk.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible experiments.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = SimulationConfig(
        num_agents=args.num_agents,
        attach_edges=args.attach_edges,
        ticks=args.ticks,
        runs=args.runs,
        initial_infected=args.initial_infected,
        hub_percent=args.hub_percent,
        random_seed=args.seed,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.ignore_phase2_normalized and args.phase2_normalized.exists():
        normalized_news = load_phase2_normalized_dataset(args.phase2_normalized)
        print(f"Loaded Phase 2 normalized dataset: {args.phase2_normalized}")
    else:
        normalized_news = load_and_normalize_datasets(
            fake_path=args.fake,
            real_path=args.real,
            telegram_path=args.telegram,
        )
        print("Loaded raw scraped datasets for feature construction.")
    featured_news = compute_news_features(normalized_news)

    phase3_payload_path = None
    if not args.force_synthetic_network:
        if args.phase3_payload.exists():
            phase3_payload_path = args.phase3_payload
        else:
            print(
                "Phase 3 payload not found; falling back to synthetic graph generation:",
                args.phase3_payload,
            )

    results = run_phase45_pipeline(
        news_df=featured_news,
        config=config,
        phase3_payload_path=phase3_payload_path,
    )

    featured_news.to_csv(output_dir / "processed_news_clusters.csv", index=False)
    results["timeline"].to_csv(output_dir / "timeline.csv", index=False)
    results["run_metrics"].to_csv(output_dir / "run_metrics.csv", index=False)
    results["average_timeline"].to_csv(output_dir / "average_timeline.csv", index=False)
    results["hub_nodes"].to_csv(output_dir / "hub_nodes.csv", index=False)

    with (output_dir / "results_summary.json").open("w", encoding="utf-8") as file:
        json.dump(results["summary"], file, indent=2, ensure_ascii=False)

    plot_average_curves(results["average_timeline"], output_dir)
    save_network_snapshot(
        graph=results["snapshot_graph"],
        state=results["snapshot_state"],
        output_path=output_dir / "network_snapshot.png",
        random_seed=args.seed,
    )

    print("Phase 4/5 simulation complete.")
    print(f"Output directory: {output_dir.resolve()}")
    print(json.dumps(results["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
