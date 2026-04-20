# Assumptions Register

## Synthetic Population
- The Moldovan information network is approximated with a Barabasi-Albert scale-free graph.
- Agent psychological traits can be represented as bounded scalar variables.
- Hub nodes are represented by a top-fraction centrality ranking.

## NLP Pipeline
- Emotional intensity is a useful proxy for misinformation spread potential.
- Translation to English before VADER scoring is acceptable as a practical approximation.
- Optional embeddings are not strictly required for the baseline pipeline.

## Simulation
- SEIZ-style transitions are a reasonable abstraction for the belief/spread process.
- Pre-bunking hubs approximates inoculation of influential actors.
- Small distortion during reshares can model message mutation.

## To Justify
- Why the chosen graph family reflects Moldova-relevant diffusion structure.
- Why emotion-linked transmissibility is a defensible proxy.
- Why heuristics or fallback modes do not invalidate comparative intervention findings.
