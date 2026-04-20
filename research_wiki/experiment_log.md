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

### Heartbeat Follow-up: Paired Effect Analysis
- Added matched-run comparison logic to the Phase 4/5 pipeline.
- New summary field:
  - `paired_run_deltas` in `results_summary.json`
- New output file on the next rerun:
  - `paired_run_comparison.csv`
- Purpose:
  - quantify how much the pre-bunking intervention improves each run relative to its paired baseline
  - support paper statements about intervention consistency, not just mean differences

### Execution Limitation
- During the heartbeat cycle at approximately `2026-04-20T12:41:48Z`, the shell command runner failed before process startup with a Windows sandbox `CreateProcessAsUserW failed: 1920` error.
- Recovery:
  - continued progress through direct source edits
  - deferred rerunning the updated simulation until shell execution becomes available again

### Continued Heartbeat Status
- During the subsequent heartbeat cycle at approximately `2026-04-20T13:14:18Z`, shell execution was still unavailable with the same Windows sandbox startup failure.
- Progress made despite the block:
  - expanded the paper draft with a statistical reporting plan for paired-run deltas
  - updated the state machine with the current blocker and the first recovery command sequence to run once execution returns

### Continued Heartbeat Status 2
- During the heartbeat cycle at approximately `2026-04-20T13:45:19Z`, shell execution again failed at process startup with the same Windows sandbox error.
- Progress made despite the block:
  - expanded the paper draft with a reproducible execution subsection and explicit parameter table
  - added `research_wiki/rerun_checklist.md` so the next successful execution cycle can immediately regenerate paired-run artifacts

### Paired-Run Rerun and Bug Fix
- Shell execution recovered during the heartbeat cycle at approximately `2026-04-20T14:01:37Z`.
- Initial rerun completed, but `paired_run_deltas` in `results_summary.json` was empty while `paired_run_comparison.csv` contained correct per-run deltas.
- Root cause:
  - the paired summary logic indexed the pivoted run-metrics table on the wrong column level
- Fix:
  - patched `simulation/phase45.py` to extract the `scenario` level explicitly with `xs(..., level="scenario")`
- Rerun command:
  - `.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\smoke\normalized_with_phase2.json --phase3-payload outputs\phase3_network\mesa_payload_phase3.json --output-dir outputs\phase45`
- Verified outputs:
  - `outputs/phase45/results_summary.json`
  - `outputs/phase45/run_metrics.csv`
  - `outputs/phase45/paired_run_comparison.csv`
- Paired-run findings:
  - mean peak infected reduction: `68.2` agents, 95% bootstrap CI `[25.49, 116.61]`
  - mean infected AUC reduction: `5902.1`, 95% bootstrap CI `[2612.17, 9420.55]`
  - mean final infected reduction: `68.2` agents, 95% bootstrap CI `[20.90, 117.50]`
  - mean peak delay: `0.9` ticks, 95% bootstrap CI `[0.6, 1.2]`
  - intervention improved peak infected in `80%` of paired runs
  - intervention improved infected AUC in `80%` of paired runs
  - intervention delayed or preserved the peak timing in `100%` of paired runs

### Checkpointing Issue
- After the paired-run rerun and documentation updates, Git status remained readable but `git add` failed with:
  - `fatal: Unable to create 'D:/projects/newsprop/NewsProp/.git/index.lock': Permission denied`
- There was no stale `index.lock` file present.
- Current interpretation:
  - the repository state is intact
  - checkpointing is deferred until Git regains write access to the index lock

### Telegram Refresh Sensitivity Run
- Imported the newer Telegram scrape from `origin/telegram_scrap` into `scraper/telegram/moldova_news_telegram.json`.
- Updated Phase 2 defaults and scraper output naming to prefer `moldova_news_telegram.json`.
- Phase 2 command:
  - `.\.venv\Scripts\python.exe phase2\pipeline.py --disable-translation --disable-embeddings --output-dir phase2\outputs\telegram_refresh`
- Phase 2 result:
  - kept `2700` records
  - rejected `16` records
- Phase 4/5 command:
  - `.\.venv\Scripts\python.exe run_phase45.py --phase2-normalized phase2\outputs\telegram_refresh\normalized_with_phase2.json --phase3-payload outputs\phase3_network\mesa_payload_phase3.json --output-dir outputs\phase45_telegram_refresh`
- Phase 4/5 result:
  - baseline peak infected: `613.0`
  - prebunked peak infected: `588.4`
  - peak reduction: `4.01%`
  - infected AUC reduction: `7.08%`
  - paired peak infected delta mean: `24.6`
  - paired infected AUC delta mean: `3272.6`
  - paired tick-of-peak delay mean: `3.1` ticks
- Interpretation:
  - the larger Telegram scrape preserves a positive average intervention effect, but the paired confidence intervals are wider and cross zero for peak infected and infected AUC, which makes this a useful sensitivity result rather than a stronger confirmation result

### Tectonic Paper Build Prep
- Added a TeX manuscript at `paper/tex/NewsProp.tex`.
- Added a build wrapper at `scripts/build_paper.ps1`.
- Added UTM guidance notes at `research_wiki/utm_guidelines.md`.
- Build probe:
  - `powershell -ExecutionPolicy Bypass -File scripts\build_paper.ps1`
- Result:
  - script parsed successfully and failed with the expected missing-binary message
  - current machine does not have `tectonic` on PATH
  - no local binary exists at `tools\tectonic\tectonic.exe`
- Follow-up:
  - provision a Tectonic binary before the paper can be compiled locally

### Checkpointing Blocker
- After the paper scaffold was added, Git checkpointing failed again because `.git` denies write access to the current user.
- Evidence:
  - `git add ...` failed with `Unable to create '.git/index.lock': Permission denied`
  - direct file creation under `.git` failed with `Access to the path ... is denied`
  - `takeown /f .git /r /d y` reported that the current user does not have ownership privileges
- Impact:
  - the LaTeX manuscript, build wrapper, and UTM guidance note remain in the working tree but are not committed yet
- Recovery path:
  - the next environment or heartbeat should either restore `.git` write access or continue by working on non-Git tasks until a writable repo is available

### TeX Sanity Check
- Verified the new manuscript structure at `paper/tex/NewsProp.tex`.
- Structural check:
  - `\begin{}` count equals `\end{}` count
  - the manuscript has a valid section and citation structure for a first-pass academic build
- Build wrapper check:
  - `scripts/build_paper.ps1` now resolves a local Tectonic binary and compiles the manuscript successfully

### Tectonic Self-Provisioning and Paper Build
- Timestamp:
  - `2026-04-20 15:20 Europe/Chisinau`
- Installed tooling:
  - `Rustup` via `winget`
  - `cargo 1.95.0`
  - official `tectonic-0.16.9-x86_64-pc-windows-msvc.zip` release asset into `tools/tectonic/`
- Root cause encountered:
  - the first `cargo install tectonic --root tools/tectonic` attempt failed because `link.exe` was unavailable on the machine
- Recovery:
  - downloaded the official Tectonic Windows binary release instead of compiling from source
  - fixed `scripts/build_paper.ps1` so it selects the full executable path from a single-item result
  - reverted the manuscript to stable LaTeX font encoding and replaced problematic Unicode characters with TeX-safe accent commands
  - shortened bibliography display text to reduce overflow
- Verification:
  - command: `powershell -ExecutionPolicy Bypass -File scripts\build_paper.ps1`
  - output: `paper/build/NewsProp.pdf`
  - status: success with residual layout warnings only
  - notable result: Tectonic now compiles the paper end to end on this machine

### Recovery Branch Checkpoint
- Timestamp:
  - `2026-04-20 15:20 Europe/Chisinau`
- Commit:
  - `0cb6fb0` - `Provision Tectonic and finalize paper build`
- Branch:
  - `autonomous/newsprop-recovery`
- Verification:
  - `git push -u origin autonomous/newsprop-recovery`
  - remote push succeeded and created the branch on GitHub
- Purpose:
  - preserve the validated paper build, the local Tectonic provisioning path, and the state/wiki updates in a remote checkpoint before starting the next experiment slice

### Translation-Enabled Phase 2 Full-Corpus Timeout
- Timestamp:
  - `2026-04-20 15:20 Europe/Chisinau`
- Command:
  - `D:\projects\newsprop\NewsProp\.venv\Scripts\python.exe phase2\pipeline.py --telegram scraper\telegram\moldova_news_telegram.json --output-dir phase2\outputs\telegram_refresh_translation --disable-embeddings`
- Input datasets:
  - refreshed Telegram scrape `scraper/telegram/moldova_news_telegram.json`
  - default fake-news and real-news inputs resolved by Phase 2
- Output directory:
  - `phase2/outputs/telegram_refresh_translation`
- Status:
  - failure by wall-clock timeout after 20 minutes
- Suspected cause:
  - translation requests across the full 2,700-record Telegram corpus are too slow for a single interactive run
- Recovery:
  - pivot to a smaller sampled Telegram smoke slice from the same refreshed corpus so translation-enabled behavior can still be measured within the runtime budget
- Final status:
  - no output artifacts were produced before timeout

### Translation-Enabled vs Disabled Phase 2 Sample Comparison
- Timestamp:
  - `2026-04-20 16:00 Europe/Chisinau`
- Sample:
  - deterministic 200-record subset from `scraper/telegram/moldova_news_telegram.json`
- Translation-enabled run:
  - command: `D:\projects\newsprop\NewsProp\.venv\Scripts\python.exe phase2\pipeline.py --telegram phase2\inputs\telegram_refresh_sample_200.json --output-dir phase2\outputs\telegram_refresh_translation_smoke --disable-embeddings`
  - runtime: `1649.26s`
  - records kept: `1272`
  - records rejected: `0`
  - translation enabled: `true`
  - global mean sentiment: `-0.0782443396226415`
  - fake mean sentiment: `-0.17162998885172798`
  - real mean sentiment: `0.14513413333333333`
- Translation-disabled run:
  - command: `D:\projects\newsprop\NewsProp\.venv\Scripts\python.exe phase2\pipeline.py --telegram phase2\inputs\telegram_refresh_sample_200.json --output-dir phase2\outputs\telegram_refresh_sample_200_no_translation --disable-translation --disable-embeddings`
  - runtime: `23.11s`
  - records kept: `1272`
  - records rejected: `0`
  - translation enabled: `false`
  - global mean sentiment: `0.6278442610062893`
  - fake mean sentiment: `0.6496999999999999`
  - real mean sentiment: `0.5755653333333333`
- Immediate interpretation:
  - enabling translation on the sample materially shifts the sentiment calibration downward and flips the fake/real ordering seen in the disabled run
  - the translation-enabled pipeline is scientifically interesting but substantially slower, so the next step should feed the sample outputs into Phase 4/5 rather than expand the translation run immediately

### Phase 4/5 on Sampled Translation Variants
- Timestamp:
  - `2026-04-20 16:30 Europe/Chisinau`
- Simulation settings:
  - `2` runs
  - `30` ticks
  - `200` agents
  - fixed Phase 3 payload: `outputs/phase3_network_smoke/mesa_payload_phase3.json`
- Translation-enabled sample output:
  - output directory: `outputs/phase45_translation_sample_smoke`
  - selected news article: `180906`
  - selected news source: `Facebook`
  - impact score: `-0.9682`
  - baseline peak infected: `186.0`
  - prebunked peak infected: `181.0`
  - peak reduction: `2.6881720430107525%`
  - infected AUC reduction: `4.066634002939735%`
  - paired peak infected delta mean: `5.0`
  - paired infected AUC delta mean: `207.5`
  - paired tick delay mean: `0.0`
- Translation-disabled sample output:
  - output directory: `outputs/phase45_sample_200_no_translation`
  - selected news article: `181039`
  - selected news source: `Facebook`
  - impact score: `0.9965`
  - baseline peak infected: `182.0`
  - prebunked peak infected: `179.0`
  - peak reduction: `1.6483516483516483%`
  - infected AUC reduction: `2.9811924769907963%`
  - paired peak infected delta mean: `3.0`
  - paired infected AUC delta mean: `149.0`
  - paired tick delay mean: `0.5`
- Immediate interpretation:
  - translation changes which article becomes the dominant fake-news driver and shifts the downstream intervention effect by roughly one percentage point on this smoke slice
  - the no-translation run is faster, but the translation-enabled run still finishes on the sampled corpus and therefore remains available for paper-grade comparison if framed as a sample-level diagnostic

### Manuscript Update After Translation Comparison
- Timestamp:
  - `2026-04-20 16:40 Europe/Chisinau`
- Change:
  - updated `paper/tex/NewsProp.tex` and `paper/NewsProp_Research_Paper.md` to describe the sampled translation comparison
- Verification:
  - rebuilt the PDF with `scripts/build_paper.ps1`
  - output: `paper/build/NewsProp.pdf`
  - status: success
- Purpose:
  - keep the manuscript synchronized with the newest evidence chain from Phase 2 through Phase 4/5

### Recovery Branch Checkpoint After Translation Comparison
- Timestamp:
  - `2026-04-20 16:40 Europe/Chisinau`
- Commit:
  - `d77196a` - `Add sampled translation comparison`
- Branch:
  - `autonomous/newsprop-recovery`
- Verification:
  - `git push` succeeded and updated the remote branch on GitHub
- Purpose:
  - preserve the sampled translation comparison, the deterministic sample input, and the updated manuscript language in a remote checkpoint
