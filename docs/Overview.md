# Master Project Architecture: Fake News Epidemic Simulation (Moldova)

## 🎯 Project Objective
Simulate the propagation of misinformation (fake news vs. real news) within a synthetic Moldovan social network using Graph Theory and the SEIZ epidemiological model. Evaluate the efficacy of "pre-bunking" (immunization) interventions to produce a Grade 10 Research Paper.

## 🏗️ Core Architecture (The 4 Layers)
1. **Data & Scraping Layer:** Raw news extraction (stiri.md, stopfals.md, Telegram).
2. **AI & NLP Layer:** Embeddings, clustering, and parameter generation (Sentence-BERT, UMAP, DBSCAN).
3. **Population & Network Layer:** Synthetic agent generation and scale-free graphing (NetworkX).
4. **Simulation Layer:** Agent-based state transitions using the SEIZ model variant (Mesa).
5. **Analysis & Visualization Layer:** Graphing results and compiling the research paper (Matplotlib, Manim).

## 📦 Global Technical Requirements
* **Language:** Python 3.10+
* **Version Control:** GitHub (Strict branching: `feature/scraper`, `feature/nlp`, `feature/sim`)
* **Core Libraries:** `requests`, `drissionpage`, `telethon`, `sentence-transformers`, `umap-learn`, `scikit-learn`, `networkx`, `mesa`, `matplotlib`, `pandas`.