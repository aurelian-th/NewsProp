# Phase 3 Network Engine

This module implements NewsProp Phase 3 (Population and Network Layer):

- Generate a scale-free Moldova-like social graph with Barabasi-Albert.
- Create agent profiles with realistic ranges for:
  - age (18-80)
  - critical_thinking (0.0-1.0)
  - media_trust (0.0-1.0)
  - preferred_channel (Mouth, Social, TV)
- Compute betweenness and eigenvector centrality.
- Tag top 5% of nodes as hub nodes.
- Export graph and agent data in formats ready for Phase 4 simulation.

## Run

From NewsProp root:

```bash
python run_phase3_network.py --nodes 1000 --m 3 --seed 20260477
```

Optional arguments:

- `--hub-fraction 0.05`
- `--betweenness-k 256` (sampled approximation for larger networks)
- `--output-dir outputs/phase3_network`

## Output Files

- `moldova_network.graphml`
- `adjacency_matrix.csv.gz`
- `edge_list.csv`
- `agent_profiles.csv`
- `agent_profiles.json`
- `mesa_payload_phase3.json`
- `network_summary.json`

## Calibration Sources

The generated summary embeds source metadata from:

- NetworkX algorithm docs
- World Bank Moldova indicators (population, age structure, internet, urbanization)
- Moldova media-audience reports (IJC, MOM)

This keeps the synthetic assumptions transparent and auditable.
