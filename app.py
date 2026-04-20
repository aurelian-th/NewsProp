import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

try:
    from simulation.phase45 import (
        SimulationConfig,
        compute_news_features,
        load_and_normalize_datasets,
        run_single_simulation,
        build_population_graph,
    )
except ModuleNotFoundError:
    import sys
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from simulation.phase45 import (
        SimulationConfig,
        compute_news_features,
        load_and_normalize_datasets,
        run_single_simulation,
        build_population_graph,
    )

st.set_page_config(page_title="Fake News Spread Simulator", layout="wide")

@st.cache_data
def load_data():
    real_path = Path("scraper/real/stirimd_dataset.json")
    fake_path = Path("scraper/fake/stopfals_final_dataset.json")
    telegram_path = Path("scraper/telegram/moldova_news_50.json")

    normalized = load_and_normalize_datasets(fake_path, real_path, telegram_path)
    featured = compute_news_features(normalized)
    return featured

st.title("Fake News Propagation Simulator (SEIZ Model)")
st.write("Analyze the spread of news through a simulated Moldovan ecosystem.")

try:
    dataset = load_data()
    st.success(f"Loaded {len(dataset)} articles from stiri.md, stopfals.md, and Telegram.")
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    dataset = pd.DataFrame()

if not dataset.empty:
    # Sidebar
    st.sidebar.header("Simulation Settings")
    
    search_query = st.sidebar.text_input("Search Headline", "")
    
    if search_query:
        matches = dataset[dataset["headline"].str.contains(search_query, case=False, na=False)]
    else:
        matches = dataset

    if matches.empty:
        st.warning("No articles found.")
        st.stop()

    article_idx = st.sidebar.selectbox("Select Article to Simulate", matches.index, format_func=lambda x: f"{matches.loc[x, 'headline'][:60]}... ({'Fake' if matches.loc[x, 'is_fake'] else 'Real'})")
    article = matches.loc[article_idx]

    st.sidebar.subheader("Network Settings")
    use_synthetic = st.sidebar.checkbox("Use Built-in BA Network (Ignore Phase 3)", value=True)
    num_agents = st.sidebar.slider("Number of Agents", 100, 2000, 500)
    ticks = st.sidebar.slider("Simulation Ticks", 10, 100, 50)
    intervene = st.sidebar.checkbox("Apply Pre-bunking (Immunize Hubs)", value=False)
    hub_percent = st.sidebar.slider("Hub Pre-bunk Ratio", 0.01, 0.20, 0.05) if intervene else 0.05

    st.subheader(f"Selected Article: {article['headline']}")
    cols = st.columns(4)
    cols[0].metric("Type", "Fake" if article["is_fake"] else "Real News")
    cols[1].metric("Source", article["source"])
    cols[2].metric("Beta (Transmission)", f"{article['transmission_probability']:.2f}")
    cols[3].metric("Emotional Impact", f"{article['emotional_intensity']:.2f}")

    if st.button("▶ Run Simulation"):
        with st.spinner("Setting up network and running simulation..."):
            rng = np.random.default_rng(42)
            
            config = SimulationConfig(
                num_agents=num_agents,
                attach_edges=3,
                ticks=ticks,
                runs=1,
                initial_infected=max(1, int(num_agents * 0.01)),
                hub_percent=hub_percent,
                random_seed=42,
            )

            # Setup Graph
            app_graph, app_agents, hub_nodes = build_population_graph(config=config, rng=rng)

            timeline, final_state = run_single_simulation(
                graph=app_graph,
                agents=app_agents,
                news_item=article,
                config=config,
                rng=rng,
                prebunk_hubs=intervene,
                hub_nodes=hub_nodes,
            )

            st.success("Simulation Complete!")

            # Visualization
            st.subheader("Infection Curve")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(timeline["tick"], timeline["S"], label="Susceptible", color="gray")
            ax.plot(timeline["tick"], timeline["E"], label="Exposed", color="orange")
            ax.plot(timeline["tick"], timeline["I"], label="Infected (Spreading)", color="red")
            ax.plot(timeline["tick"], timeline["Z"], label="Skeptic (Immune)", color="green")
            ax.set_xlabel("Time (Ticks)")
            ax.set_ylabel("Population")
            ax.legend()
            ax.grid(alpha=0.3)
            st.pyplot(fig)

            # Draw Network
            st.subheader("Final Network State")
            color_map = {0: "gray", 1: "orange", 2: "red", 3: "green"}
            node_colors = [color_map.get(int(final_state[node_id]), "gray") for node_id in app_graph.nodes]

            fig_net, ax_net = plt.subplots(figsize=(10, 6))
            pos = nx.spring_layout(app_graph, seed=42)
            nx.draw_networkx_nodes(app_graph, pos, node_size=20, node_color=node_colors, alpha=0.8, ax=ax_net)
            nx.draw_networkx_edges(app_graph, pos, alpha=0.1, ax=ax_net)
            ax_net.axis("off")
            st.pyplot(fig_net)

st.markdown("---")
st.markdown("*NewsProp Simulator - Final Phase Deliverable*")