# Phase Map

## Phase 1: Data Collection
- Goal: collect fake, real, and social-channel news from Moldova-relevant sources.
- Existing implementation:
  - `scraper/fake/`
  - `scraper/real/`
  - `scraper/telegram/`
- Evidence:
  - fake dataset from StopFals
  - real-news dataset from Stiri.md
  - Telegram dataset on `main` and an expanded dataset on `origin/telegram_scrap`
- Open needs:
  - unify schema guarantees across scrapers
  - document rerun instructions and data freshness policy

## Phase 2: NLP and Feature Extraction
- Goal: normalize records, translate when needed, score emotion, and export metrics used downstream.
- Existing implementation:
  - `phase2/pipeline.py`
  - `phase2/outputs/artifacts/`
- Strength:
  - already produces confidence intervals and empirical calibration artifacts
- Open needs:
  - integrate these outputs directly into simulation inputs
  - validate whether translation and VADER choices are acceptable for Moldovan multilingual content

## Phase 3: Synthetic Network
- Goal: generate a Moldova-inspired social graph with realistic agent attributes and hub detection.
- Existing implementation:
  - `network/pipeline.py`
  - `run_phase3_network.py`
- Open needs:
  - validate calibration assumptions
  - capture why chosen distributions are acceptable in the paper

## Phase 4: Propagation Simulation
- Goal: simulate SEIZ-style spread and intervention effects.
- Existing implementation:
  - `simulation/phase45.py`
  - `run_phase45.py`
- Open needs:
  - replace or augment heuristic feature derivation with Phase 2 data
  - add stronger run metadata and validation

## Phase 5: Analysis and Paper
- Goal: turn repeated simulations into scientific claims and publication-ready visuals.
- Existing implementation:
  - summary JSON and plotting in `run_phase45.py`
  - `docs/PRESENTATION.md`
- Open needs:
  - confidence intervals for simulation outcomes
  - explicit experiment matrix
  - final paper in academic structure
