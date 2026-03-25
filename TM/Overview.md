# Master Project Architecture: Fake News Epidemic Simulation (Moldova)

## 🎯 Project Objective
Simulate the propagation of misinformation (fake news vs. real news) within a synthetic Moldovan social network using Graph Theory and the SEIZ epidemiological model. Evaluate the efficacy of "pre-bunking" (immunization) interventions to produce a Grade 10 Research Paper.

## 🏗️ Core Architecture (The 4 Layers)
1. **Data & Scraping Layer:** Raw news extraction (ProTV, stopfals.md, Telegram).
2. **AI & NLP Layer:** Embeddings, clustering, and parameter generation (Sentence-BERT, UMAP, DBSCAN).
3. **Population & Network Layer:** Synthetic agent generation and scale-free graphing (NetworkX).
4. **Simulation Layer:** Agent-based state transitions using the SEIZ model variant (Mesa).

## 🧑‍💻 Team Roles & Task Distribution
* **Aurel:** Data Pipeline, Web Scraping (`parse.bot`, `DrissionPage`, `Telethon`).
* **Gabi:** ML & NLP Pipeline (Sentence-BERT, UMAP, DBSCAN, feature extraction).
* **Lucian:** Agentic Simulation Engine (Mesa, SEIZ math implementation).
* **Daniel & Victor:** Network Topology (NetworkX, Barabasi-Albert graph), Visualization (Manim/Matplotlib), Research Paper Formatting.

## 📦 Global Technical Requirements
* **Language:** Python 3.10+
* **Version Control:** GitHub (Strict branching: `feature/scraper`, `feature/nlp`, `feature/sim`)
* **Core Libraries:** `requests`, `drissionpage`, `telethon`, `sentence-transformers`, `umap-learn`, `scikit-learn`, `networkx`, `mesa`, `matplotlib`, `pandas`.