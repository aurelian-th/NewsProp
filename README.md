# NewsProp

> A reproducible research pipeline for modeling how fake news spreads through a synthetic Moldovan social network, and how pre-bunking hub nodes can reduce that spread.

## What This Branch Adds

- Phase 3: a calibrated scale-free social network builder with realistic agent profiles.
- Phase 4: a SEIZ-style simulation engine that spreads a selected news item across the network.
- Phase 5: analysis and visualization outputs that compare a baseline run against a pre-bunked intervention.
- A small Windows startup shim so pandas-based imports do not hang on this machine because of a slow WMI probe.

## Why It Matters

The project turns a broad idea into something measurable:

- a network with hubs and heterogeneous agents,
- a simulation that tracks S, E, I, and Z states over time,
- and a direct intervention test that shows whether targeting hubs changes the outcome.

That gives you a concrete story for a presentation:

- the spread is not random,
- the network structure matters,
- and a targeted intervention has measurable impact.

## Architecture

### Phase 1
Scrape fake, real, and Telegram news datasets into a shared JSON-like structure.

### Phase 2
Normalize each article into derived features such as controversy score, emotional intensity, and transmission probability.

### Phase 3
Build a Barabasi-Albert network and assign each node a profile:

- age
- critical thinking
- media trust
- preferred channel
- hub score

The default output is a 1,000-node, 2,991-edge network with the top 5 percent tagged as hubs.

### Phase 4
Run a SEIZ-style agent simulation:

- `S` = susceptible
- `E` = exposed
- `I` = infected
- `Z` = skeptic

The model supports:

- local neighbor spread,
- channel-based spread,
- broadcast effects,
- and a small distortion effect that nudges the news parameters as it is shared.

### Phase 5
Compare baseline and pre-bunked scenarios, then export:

- `timeline.csv`
- `average_timeline.csv`
- `hub_nodes.csv`
- `results_summary.json`
- `infected_curve_comparison.png`
- `state_trajectories.png`
- `network_snapshot.png`

## Quick Start

From the `NewsProp` folder:

```powershell
python run_phase3_network.py
python run_phase45.py --phase3-payload outputs/phase3_network/mesa_payload_phase3.json
```

For the smaller smoke version:

```powershell
python run_phase3_network.py --nodes 200 --output-dir outputs/phase3_network
python run_phase45.py --runs 2 --ticks 30 --num-agents 200 --output-dir outputs/phase45 --phase3-payload outputs/phase3_network/mesa_payload_phase3.json
```

## Verified Results

### Phase 3 default run

- 1,000 nodes
- 2,991 edges
- average degree: 5.982
- degree Gini: 0.3796
- hub nodes: 50
- hub degree share: 24.86 percent
- runtime: about 5.2 seconds on this machine

### Phase 4/5 default run

- 1,000 agents
- 10 runs
- 80 ticks
- baseline peak infected: 778.6
- pre-bunked peak infected: 736.9
- peak reduction: 5.36 percent
- infected AUC reduction: 6.41 percent
- runtime: about 50.1 seconds on this machine

These numbers are from the current branch after verification.

## What Can Be Improved Next

- Replace the heuristic Phase 2 feature extraction with actual embeddings and clustering.
- Tighten calibration against more empirical data and run larger Monte Carlo sweeps.
- Add confidence intervals, not just averages.
- Produce a cleaner slide deck or PDF report from the same metrics.
- Add caching for heavy centrality computations if the network grows larger.
- Add a single configuration file so the whole pipeline is easier to reproduce.

## Presentation Angle

If you want the short version:

1. We built a realistic network of Moldovan agents.
2. We simulated fake-news spread with SEIZ states.
3. We tested whether pre-bunking hub nodes helps.
4. It does help, and the effect is measurable.

If you want the stronger version:

- the model is reproducible,
- the outputs are visual,
- and the intervention story is easy to explain in one slide.

## Repo Notes

- Generated outputs are ignored by Git so the branch stays clean.
- The project uses `networkx`, `numpy`, `pandas`, `matplotlib`, and `scikit-learn`.
- The Windows bootstrap is intentionally small and only exists to avoid the pandas import stall on this machine.
