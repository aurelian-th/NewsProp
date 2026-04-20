# Statistical Reporting Plan

## Purpose
This file defines how NewsProp results should be reported in the final paper so that the intervention claim is data-driven and not limited to single-run anecdotes.

## Core Outcome Metrics
- peak infected
- infected area under the curve
- final infected
- tick of peak

## Reporting Levels
### Scenario Level
- baseline mean for each metric
- prebunked-hubs mean for each metric
- 95% bootstrap confidence interval for each scenario mean

### Paired-Run Level
- per-run delta: baseline minus prebunked for:
  - peak infected
  - infected AUC
  - final infected
- per-run delay: prebunked tick of peak minus baseline tick of peak
- share of runs with positive intervention effect
- share of runs with non-negative intervention effect

## Narrative Use
- Scenario means answer: "Does the intervention help on average?"
- Paired deltas answer: "Does the intervention help consistently across matched runs?"

## Pending Artifact Refresh
The paired-analysis refresh has now been completed successfully. The following artifacts should be treated as the current reporting baseline:
- `outputs/phase45/results_summary.json`
- `outputs/phase45/run_metrics.csv`
- `outputs/phase45/paired_run_comparison.csv`

## Current Verified Paired Findings
- mean peak infected delta: `68.2`
- 95% bootstrap CI for peak infected delta: `[25.49, 116.61]`
- mean infected AUC delta: `5902.1`
- 95% bootstrap CI for infected AUC delta: `[2612.17, 9420.55]`
- mean final infected delta: `68.2`
- 95% bootstrap CI for final infected delta: `[20.90, 117.50]`
- mean tick-of-peak delay: `0.9`
- 95% bootstrap CI for tick-of-peak delay: `[0.6, 1.2]`
- positive intervention share:
  - `0.8` for peak infected
  - `0.8` for infected AUC
  - `0.8` for final infected
  - `1.0` non-negative share for peak delay

## Telegram Refresh Sensitivity Findings
- mean peak infected delta: `24.6`
- 95% bootstrap CI for peak infected delta: `[-18.50, 67.31]`
- mean infected AUC delta: `3272.6`
- 95% bootstrap CI for infected AUC delta: `[-67.77, 6516.58]`
- mean final infected delta: `24.6`
- mean tick-of-peak delay: `3.1`
- 95% bootstrap CI for tick-of-peak delay: `[2.1, 4.2]`
- positive intervention share:
  - `0.7` for peak infected
  - `0.7` for infected AUC
  - `0.7` for final infected
  - `1.0` non-negative share for tick delay

## Paper Integration Targets
- Abstract: one sentence on average reduction
- Results: table with means and bootstrap intervals
- Discussion: paragraph on paired-run consistency
- Limitations: note that synthetic assumptions still constrain external validity
