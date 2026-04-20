# Experiment Log

## 2026-04-20

### Initialization
- Cloned repository and analyzed remote branches: `main`, `phase3-4`, `telegram_scrap`.
- Confirmed the effective five-phase roadmap from docs and code.
- Merged the Phase 3-5 implementation branch into the active integration branch.

### Environment Setup
- Created `.venv` with the scientific stack from `requirements.txt`.
- Installed `networkx`, `numpy`, `pandas`, `scikit-learn`, `matplotlib`, `vaderSentiment`, `deep-translator`, `langdetect`, `sentence-transformers`, and related dependencies successfully on Python 3.14.

### Automation
- Created a thread heartbeat automation named `NewsProp Loop`.
- Cadence: every 30 minutes.
- Purpose: read `STATE_MACHINE.md`, execute the current intent, update state and research logs, and continue.

### Smoke Tests
- Phase 2 command:
  - `.\.venv\Scripts\python.exe phase2\pipeline.py --disable-translation --disable-embeddings --output-dir phase2\outputs\smoke`
- Phase 2 result:
  - kept `1121` records
  - rejected `1` record
- Phase 3 command:
  - `.\.venv\Scripts\python.exe run_phase3_network.py --nodes 200 --output-dir outputs\phase3_network_smoke`
- Phase 3 result:
  - smoke network and Mesa payload generated successfully
- Phase 4/5 command:
  - `.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\smoke\normalized_with_phase2.json --runs 2 --ticks 30 --num-agents 200 --output-dir outputs\phase45_smoke_phase2 --phase3-payload outputs\phase3_network_smoke\mesa_payload_phase3.json`
- Phase 4/5 result:
  - feature source: `phase2_normalized`
  - peak infected reduction: `3.65%`
  - infected AUC reduction: `4.82%`

### Integration Patch
- Modified `run_phase45.py` to prefer a Phase 2 normalized dataset when available.
- Modified `simulation/phase45.py` to load Phase 2-normalized records and preserve `impact_score` and Phase 2 emotional intensity in the simulation feature construction path.

### Full Experiment 001
- Phase 3 command:
  - `.\.venv\Scripts\python.exe run_phase3_network.py --nodes 1000 --output-dir outputs\phase3_network`
- Network result:
  - nodes: `1000`
  - edges: `2991`
  - hub nodes: `50`
  - hub degree share: `24.86%`
- Phase 4/5 command:
  - `.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\smoke\normalized_with_phase2.json --phase3-payload outputs\phase3_network\mesa_payload_phase3.json --output-dir outputs\phase45`
- Simulation result:
  - selected source: `Facebook`
  - feature source: `phase2_normalized`
  - baseline peak infected: `886.3`
  - prebunked peak infected: `818.1`
  - peak reduction: `7.69%`
  - infected AUC reduction: `8.68%`
  - baseline peak infected 95% bootstrap CI: `[843.20, 929.01]`
  - prebunked peak infected 95% bootstrap CI: `[784.39, 852.20]`
  - baseline infected AUC 95% bootstrap CI: `[64735.38, 70838.36]`
  - prebunked infected AUC 95% bootstrap CI: `[59425.31, 64719.04]`

### Reproducibility Script Validation
- Added `scripts/run_full_pipeline.ps1` to bootstrap the environment and run Phases 2, 3, and 4/5 in sequence.
- Verified script with:
  - `powershell -ExecutionPolicy Bypass -File scripts\run_full_pipeline.ps1 -DisableTranslation -DisableEmbeddings -Phase3Nodes 200 -Runs 2 -Ticks 30 -Phase2OutputDir phase2/outputs/script_smoke -Phase3OutputDir outputs/phase3_network_script_smoke -Phase45OutputDir outputs/phase45_script_smoke`
- Result:
  - end-to-end automation completed successfully
  - Phase 4/5 again used `phase2_normalized` features
  - smoke reduction matched earlier validation at `3.65%` peak and `4.82%` infected AUC

### Notes
- The first verified full experiment uses Phase 2 data produced with translation and embeddings disabled for speed and robustness.
- This is sufficient for current engineering validation, but a paper-grade run should compare against a translation-enabled pipeline and add uncertainty intervals around intervention effects.
- A first paper draft now exists at `paper/NewsProp_Research_Paper.md`.
