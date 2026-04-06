# Presentation Notes

## One-Line Pitch

This project simulates how fake news spreads through a synthetic Moldovan social network and shows that pre-bunking the most central nodes can reduce the spread.

## 30-Second Version

We built a three-part research pipeline: a calibrated network of Moldovan agents, a SEIZ-style spread simulation, and a results layer that compares baseline spread against a hub-targeted pre-bunking intervention. The branch now runs end-to-end, exports plots and summary files, and gives a measurable reduction in infected reach.

## 2-Minute Version

The work starts with Phase 3, where we generate a Barabasi-Albert social graph and attach realistic agent traits such as age, critical thinking, media trust, and preferred communication channel. Phase 4 runs the spread model over that graph using S, E, I, and Z states. Phase 5 compares a baseline run against a pre-bunked run where hub nodes are skeptical from tick 0. The current default run shows a 5.36 percent reduction in peak infection and a 6.41 percent reduction in infected area under the curve.

## What Was Done

- Added a reproducible Phase 3 network builder.
- Added calibrated agent profile generation.
- Added export formats for GraphML, CSV, JSON, and Mesa-ready payloads.
- Added a Phase 4/5 simulation pipeline with baseline vs intervention scenarios.
- Added plots and summaries for presentation.
- Added docs that explain the workflow and how to run it.
- Added a small Windows compatibility shim so pandas does not hang on import in this environment.

## Measured Results

### Phase 3

- 1,000 nodes
- 2,991 edges
- 50 hub nodes
- hub degree share: 24.86 percent
- runtime: about 5.2 seconds

### Phase 4/5

- 1,000 agents
- 10 runs
- 80 ticks
- baseline peak infected: 778.6
- pre-bunked peak infected: 736.9
- peak reduction: 5.36 percent
- infected AUC reduction: 6.41 percent
- runtime: about 50.1 seconds

## Why This Is Good for a Demo

- It has a clear before/after story.
- It has numbers, not just visuals.
- It has a real intervention target: hubs.
- It exports graphs that are easy to show live.
- It feels like a research system, not just a toy script.

## What To Say About Limitations

Be honest. The strongest limitations are:

- Phase 2 still uses heuristic feature extraction instead of full embeddings and clustering.
- The network and agent calibration are synthetic, so they should be validated with more data.
- The current result is promising, but it should be backed by more runs and confidence intervals.
- The project would benefit from a cleaner config file and an automated report generator.

## What To Say About Impact

This matters because misinformation is not only about content quality, it is also about network structure and timing. The project demonstrates that a targeted intervention on central nodes can reduce spread, which is exactly the kind of idea that is easy to explain to an audience and useful for future work.

## Suggested Demo Flow

1. Open `README.md` and show the phase overview.
2. Show `docs/3. Network.md` and explain how the network is built.
3. Show `docs/4. Simulation.md` and explain the SEIZ logic.
4. Open `outputs/phase45/results_summary.json`.
5. Show `outputs/phase45/infected_curve_comparison.png`.
6. Close with the improvement list from this file.

## Good Final Line

We built a reproducible network science simulation that turns a social problem into a measurable intervention experiment.
