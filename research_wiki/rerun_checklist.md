# Rerun Checklist

## Purpose
This checklist exists so the next heartbeat with working shell access can resume immediately without rediscovering the execution sequence.

## Primary Goal
Regenerate Phase 4/5 outputs so they include the newly added paired-run analysis.

## Command Order
1. Verify shell execution works again.
2. Confirm the working tree is clean enough to run.
3. Rerun Phase 4/5 using the existing verified Phase 2 and Phase 3 artifacts:

```powershell
.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\smoke\normalized_with_phase2.json --phase3-payload outputs\phase3_network\mesa_payload_phase3.json --output-dir outputs\phase45
```

## Expected New or Refreshed Outputs
- `outputs/phase45/results_summary.json`
- `outputs/phase45/run_metrics.csv`
- `outputs/phase45/paired_run_comparison.csv`

## Verification Checks
- `results_summary.json` contains:
  - `run_metric_intervals`
  - `paired_run_deltas`
- `paired_run_comparison.csv` exists and has:
  - `peak_infected_delta`
  - `infected_auc_delta`
  - `final_infected_delta`
  - `tick_of_peak_delay`

## Follow-up After Successful Rerun
1. Update `research_wiki/experiment_log.md` with paired-delta findings.
2. Update `paper/NewsProp_Research_Paper.md` with matched-run consistency language.
3. Commit the refreshed outputs and documentation changes if the working tree is stable.
