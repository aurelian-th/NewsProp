# NewsProp Autonomous State Machine

## Mission
Deliver a fully functional Moldova-focused misinformation propagation simulator and the research assets needed to turn the implementation into a university-grade paper for the Technical University of Moldova.

## Operating Loop
1. Observe: read this file first.
2. Think: choose the next smallest measurable intent that advances product completion or research validity.
3. Act: implement, run, measure, and save artifacts.
4. Update: record results, failures, pivots, and the next intent before stopping.

## Branch + Repo Baseline
- Active working branch: `autonomous/integration-loop`
- Remote branches analyzed:
  - `origin/main`: contains Phase 1 scraping assets and the active Phase 2 NLP pipeline.
  - `origin/phase3-4`: contains the only implemented Phase 3 network builder and Phase 4/5 simulation pipeline.
  - `origin/telegram_scrap`: contains an expanded Telegram scraping branch and larger Telegram dataset.
- Integration status:
  - Merged `origin/phase3-4` into `autonomous/integration-loop`.
  - Preserved Phase 2 assets from `main`.
  - Confirmed repository now spans Phases 1 through 5 in code or documentation.

## Five-Phase Map
1. Phase 1: Data collection and scraping.
   - Implemented assets: fake-news scraper, real-news scraper, Telegram scraper, existing datasets.
   - Gap: reproducible rerun workflow and schema validation are not yet unified across all scrapers.
2. Phase 2: NLP and impact scoring.
   - Implemented assets: normalization, language detection, translation, VADER scoring, optional embeddings, CI/calibration outputs.
   - Gap: later simulation branch currently computes its own heuristic features instead of consuming Phase 2 outputs directly.
3. Phase 3: Population and network modeling.
   - Implemented assets: Barabasi-Albert graph builder, agent profile synthesis, hub detection, payload export.
   - Gap: calibration assumptions need to be documented and verified for paper use.
4. Phase 4: Simulation engine.
   - Implemented assets: SEIZ-like spread engine, channel effects, hub prebunking intervention, distortion effect, timeline collection.
   - Gap: needs tighter integration with Phase 2 features, more validation, and repeatable experiments.
5. Phase 5: Analysis and paper production.
   - Implemented assets: plots, summary metrics, snapshot export, presentation draft in branch docs.
   - Gap: full research paper, experiment matrix, uncertainty reporting, and final narrative are still missing.

## Current Assessment
- Already built:
  - Multi-source data scraping foundation.
  - Phase 2 NLP pipeline with measurable outputs.
  - Phase 3-5 prototype pipeline on the merged branch.
- Missing or weak:
  - One-command reproducible environment setup.
  - End-to-end pipeline that explicitly links Phase 2 outputs into Phase 4 inputs.
  - Scientific logging for experiments and model assumptions.
  - Final paper structure and evidence chain.

## Current Execution Plan
1. Preserve the new Phase 2 -> Phase 4/5 integration path and reproducible runner scripts.
2. Expand experiment logging and uncertainty reporting for simulation outcomes.
3. Draft the first research-paper chapter set from current artifacts.
4. Improve data freshness and scraper rerun documentation.
5. Run larger or variant experiments as needed for stronger claims.
6. Synthesize figures, tables, and methodology into the final paper.

## Latest Completed Intent
- Cloned the repository into `D:\projects\newsprop\NewsProp`.
- Fetched and analyzed all remote branches.
- Mapped the five project phases from docs and code.
- Created a dedicated integration branch.
- Merged the `origin/phase3-4` branch into the active branch.
- Added root state tracking, research wiki scaffolding, automation documentation, and a unified dependency manifest.
- Registered an active thread heartbeat automation named `NewsProp Loop`.
- Installed project dependencies into `.venv`.
- Verified Phase 2, Phase 3, and Phase 4/5 smoke runs successfully.
- Patched `run_phase45.py` and `simulation/phase45.py` so Phase 4/5 can consume Phase 2 normalized outputs directly.
- Ran a 1,000-node baseline plus prebunking experiment using Phase 2-derived features.
- Added `scripts/run_full_pipeline.ps1` to execute Phases 2, 3, and 4/5 in one command.
- Created the first working paper draft at `paper/NewsProp_Research_Paper.md`.

## Current Intent
Push the project from engineering validation into paper-grade analysis by adding stronger uncertainty reporting and expanding the draft paper with better methodology and result framing.

## Next Intent
Add simulation uncertainty estimates and reflect them in the paper draft and research wiki.

## Risks and Pivots
- Python 3.14 compatibility remains a risk for less common scientific dependencies, even though the current stack installed successfully.
- Full translation-enabled Phase 2 runs may be slower or rate-limited; the current validated experiment used `--disable-translation --disable-embeddings`.
- The current result is a strong baseline but still needs uncertainty reporting across intervention outcomes for paper-grade rigor.
- Scraper refresh and dataset provenance documentation still need tightening before final submission.

## Latest Measured Results
- Phase 2 smoke pipeline:
  - command: `.\.venv\Scripts\python.exe phase2\pipeline.py --disable-translation --disable-embeddings --output-dir phase2\outputs\smoke`
  - kept records: `1121`
  - rejected records: `1`
- Phase 3 smoke pipeline:
  - command: `.\.venv\Scripts\python.exe run_phase3_network.py --nodes 200 --output-dir outputs\phase3_network_smoke`
  - output: smoke payload generated successfully
- Phase 4/5 smoke pipeline using Phase 2 outputs:
  - command: `.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\smoke\normalized_with_phase2.json --runs 2 --ticks 30 --num-agents 200 --output-dir outputs\phase45_smoke_phase2 --phase3-payload outputs\phase3_network_smoke\mesa_payload_phase3.json`
  - peak reduction: `3.65%`
  - infected AUC reduction: `4.82%`
- Full Phase 3 + Phase 4/5 run:
  - network nodes: `1000`
  - edges: `2991`
  - hub nodes: `50`
  - baseline peak infected: `886.3`
  - prebunked peak infected: `818.1`
  - peak reduction: `7.69%`
  - infected AUC reduction: `8.68%`
  - baseline peak infected 95% bootstrap CI for mean: `[843.20, 929.01]`
  - prebunked peak infected 95% bootstrap CI for mean: `[784.39, 852.20]`
  - baseline infected AUC 95% bootstrap CI for mean: `[64735.38, 70838.36]`
  - prebunked infected AUC 95% bootstrap CI for mean: `[59425.31, 64719.04]`

## Experiment Logging Rules
- Every run must record:
  - command
  - input datasets
  - random seed
  - output directory
  - success/failure
  - key numeric results
- Every failure must record:
  - traceback summary
  - suspected cause
  - remediation attempt
  - final status

## Update Template
### Timestamp
`YYYY-MM-DD HH:MM TZ`

### Completed
- item

### Evidence
- file path or output directory

### Failures / Recoveries
- issue and response

### Next Intent
- smallest next task
