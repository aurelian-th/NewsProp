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

## Translation Effect on Sampled Telegram Slice
- sample: deterministic 200-record subset from the refreshed Telegram corpus
- translation-enabled global mean sentiment: `-0.0782443396226415`
- translation-disabled global mean sentiment: `0.6278442610062893`
- delta between translation-enabled and translation-disabled global means: `-0.7060886006289308`
- interpretation:
  - translation changes the Phase 2 calibration substantially on this slice, so any paper claim about sentiment or downstream diffusion should explicitly name the translation setting used
  - the translation-enabled path is too slow for the full corpus in one interactive run, so the sample should be treated as a diagnostic comparison rather than a full replacement for the corpus-wide baseline

## Phase 4/5 Sample Simulation Comparison
- simulation setting:
  - `2` runs
  - `30` ticks
  - `200` agents
  - fixed Phase 3 smoke payload
- translation-enabled sample:
  - peak reduction: `2.6881720430107525%`
  - infected AUC reduction: `4.066634002939735%`
  - paired peak infected delta mean: `5.0`
  - paired infected AUC delta mean: `207.5`
  - paired tick delay mean: `0.0`
- translation-disabled sample:
  - peak reduction: `1.6483516483516483%`
  - infected AUC reduction: `2.9811924769907963%`
  - paired peak infected delta mean: `3.0`
  - paired infected AUC delta mean: `149.0`
  - paired tick delay mean: `0.5`
- interpretation:
  - translation-enabled preprocessing slightly strengthens the measured intervention effect on this smoke slice, but the dominant difference is still the sentiment calibration shift in Phase 2
  - because the two Phase 2 runs selected different dominant articles, the comparison should be described as a pipeline sensitivity test rather than a pure ablation of translation alone

## Paper Integration Targets
- Abstract: one sentence on average reduction
- Results: table with means and bootstrap intervals
- Discussion: paragraph on paired-run consistency
- Limitations: note that synthetic assumptions still constrain external validity
