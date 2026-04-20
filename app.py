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

st.set_page_config(page_title="NewsProp Analytics", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container { padding-top: 2rem; }
div[data-testid="stMetricValue"] { font-weight: bold; color: #e53935; }
h1 { font-weight: 300; font-family: 'Segoe UI', sans-serif; }
div[data-testid="stTabs"] button { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    real_path = Path("scraper/real/stirimd_dataset.json")
    fake_path = Path("scraper/fake/stopfals_final_dataset.json")
    telegram_path = Path("scraper/telegram/moldova_news_50.json")

    normalized = load_and_normalize_datasets(fake_path, real_path, telegram_path)
    featured = compute_news_features(normalized)
    return featured

@st.cache_data(show_spinner=False)
def get_tsne_clusters(df):
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    features = ["views", "likes", "shares", "comments", "top_comment_count", "controversy_score", "emotional_intensity"]
    X = df[features].fillna(0).values
    X_scaled = StandardScaler().fit_transform(X)
    tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=500)
    X_2d = tsne.fit_transform(X_scaled)
    df_tsne = df.copy()
    df_tsne["tSNE_1"] = X_2d[:, 0]
    df_tsne["tSNE_2"] = X_2d[:, 1]
    return df_tsne

col1, col2 = st.columns([3, 1])
with col1:
    st.title("NewsProp Analytics & Simulation System")
with col2:
    st.markdown("<div style='text-align:right; margin-top:20px;'><span style='color:gray'>Moldovan Digital Epidemic Tracker</span></div>", unsafe_allow_html=True)
st.markdown("---")

try:
    with st.spinner("Initializing system constraints and dataset models..."):
        dataset = load_data()
        dataset = get_tsne_clusters(dataset)
except Exception as e:
    st.error(f"System Error (Data Access Layer): {e}")
    dataset = pd.DataFrame()

if not dataset.empty:
    st.sidebar.title("Configuration")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Data Parameterization")
    mode = st.sidebar.radio("Injection Mode", ["Historical Record", "Synthetic Payload"])
    
    if mode == "Historical Record":
        type_filter = st.sidebar.selectbox("Filter Class", ["All Content", "Flagged Misinformation", "Verified Sources"])
        search_query = st.sidebar.text_input("Query Database", "")
        
        matches = dataset.copy()
        if type_filter == "Flagged Misinformation":
            matches = matches[matches["is_fake"] == True]
        elif type_filter == "Verified Sources":
            matches = matches[matches["is_fake"] == False]
            
        if search_query:
            matches = matches[matches["headline"].str.contains(search_query, case=False, na=False)]

        if matches.empty:
            st.warning("No matching entities found in current record set.")
            st.stop()

        article_idx = st.sidebar.selectbox(
            "Select Origin Entity", 
            matches.index, 
            format_func=lambda x: f"[{'Disinfo' if matches.loc[x, 'is_fake'] else 'Verified'}] {matches.loc[x, 'headline'][:40]}..."
        )
        article = matches.loc[article_idx].to_dict()
    
    else:
        custom_title = st.text_input("Origin Payload Title", "National infrastructure failure reports spreading in major hubs")
        custom_desc = st.text_area("Content Payload (NLP Analyzed)", "Scientists and experts issue warning regarding the new infrastructure...")
        is_fake = st.checkbox("Flag as Disinformation?", value=True)
        
        if not custom_title:
            st.warning("Entity payload requires title field to evaluate sentiment vector.")
            st.stop()
            
        custom_df = pd.DataFrame([{
            "headline": custom_title,
            "combined_text": f"{custom_title} {custom_desc}",
            "is_fake": is_fake,
            "source": "Synthetic_Injection",
            "source_type": "fake" if is_fake else "real",
            "views": dataset["views"].median(),
            "likes": dataset["likes"].median(),
            "shares": dataset["shares"].median(),
            "comments": dataset["comments"].median(),
            "top_comment_count": dataset["top_comment_count"].median(),
            "has_debunk_context": not is_fake
        }])
        
        with st.spinner("Running NLP embedding vectors..."):
            featured_custom = compute_news_features(custom_df)
        article = featured_custom.iloc[0].to_dict()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Topological Parameters")
    num_agents = st.sidebar.number_input("Population Size", min_value=100, max_value=5000, value=500, step=100)
    ticks = st.sidebar.number_input("Epoch Duration", min_value=10, max_value=200, value=75, step=10)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Intervention Controls")
    intervene = st.sidebar.checkbox("Activate Pre-bunking Defense Matrix", value=False)
    hub_percent = st.sidebar.slider("Hub Immunization Coverage (%)", 1, 20, 5) / 100.0 if intervene else 0.05

    tab_sim, tab_data = st.tabs(["[Module 1] Propagation Simulation", "[Module 2] Multidimensional Clustering"])
    
    with tab_sim:
        st.subheader("Entity Metadata", divider="gray")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Classification", "Disinformation" if article["is_fake"] else "Verified")
        c2.metric("Domain Node", article["source"])
        c3.metric("Emotional Coefficient", f"{article['emotional_intensity']:.3f}")
        c4.metric("Base Spread Vector (Beta)", f"{article['transmission_probability']:.3f}")

        st.markdown(f"**Payload Fragment:** {article['headline']}")
        
        if st.button("▶ Execute Propagation Model", type="primary", use_container_width=True):
            with st.spinner("Running SEIZ mathematical topological simulation..."):
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

                app_graph, app_agents, hub_nodes = build_population_graph(config=config, rng=rng)
                timeline, final_state = run_single_simulation(
                    graph=app_graph, agents=app_agents, news_item=article,
                    config=config, rng=rng, prebunk_hubs=intervene, hub_nodes=hub_nodes,
                )

                g1, g2 = st.columns(2)
                
                with g1:
                    st.subheader("Population Dynamics (SEIZ Curve)")
                    fig, ax = plt.subplots(figsize=(6, 4))
                    fig.patch.set_alpha(0.0)
                    ax.set_facecolor('none')
                    ax.plot(timeline["tick"], timeline["S"], label="Susceptible", color="#9e9e9e", linewidth=2)
                    ax.plot(timeline["tick"], timeline["E"], label="Exposed", color="#fb8c00", linewidth=2)
                    ax.plot(timeline["tick"], timeline["I"], label="Infected (Spreading)", color="#e53935", linewidth=2)
                    ax.plot(timeline["tick"], timeline["Z"], label="Skeptic (Firewall)", color="#43a047", linewidth=2)
                    ax.set_xlabel("Epoch / Time")
                    ax.set_ylabel("Node Count")
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.legend(frameon=False)
                    ax.grid(alpha=0.1)
                    st.pyplot(fig)

                with g2:
                    st.subheader("Final Topological State")
                    color_map = {0: "#9e9e9e", 1: "#fb8c00", 2: "#e53935", 3: "#43a047"}
                    node_colors = [color_map.get(int(final_state[node_id]), "#9e9e9e") for node_id in app_graph.nodes]
                    
                    fig_net, ax_net = plt.subplots(figsize=(6, 4))
                    fig_net.patch.set_alpha(0.0)
                    pos = nx.spring_layout(app_graph, seed=42)
                    nx.draw_networkx_nodes(app_graph, pos, node_size=15, node_color=node_colors, alpha=0.85, ax=ax_net)
                    nx.draw_networkx_edges(app_graph, pos, alpha=0.08, edge_color="#b0bec5", ax=ax_net)
                    ax_net.axis("off")
                    st.pyplot(fig_net)

    with tab_data:
        st.subheader("Global Information Environment State (t-SNE Projection)", divider="gray")
        
        opt_col, _ = st.columns([1, 2])
        with opt_col:
            color_col = st.selectbox("Display Dimension Overlay:", ["Classification (Disinfo/Verified)", "Source Domain", "Emotional Intensity Map", "Transmission Velocity (Beta) Map"])

        fig_tsne, ax_tsne = plt.subplots(figsize=(10, 5))
        fig_tsne.patch.set_alpha(0.0)
        ax_tsne.set_facecolor('none')
        
        if color_col == "Classification (Disinfo/Verified)":
            fake_mask = dataset["is_fake"] == True
            real_mask = dataset["is_fake"] == False
            ax_tsne.scatter(dataset.loc[fake_mask, "tSNE_1"], dataset.loc[fake_mask, "tSNE_2"], color="#e53935", label="Disinformation", alpha=0.7, s=20, edgecolors='none')
            ax_tsne.scatter(dataset.loc[real_mask, "tSNE_1"], dataset.loc[real_mask, "tSNE_2"], color="#1e88e5", label="Verified", alpha=0.7, s=20, edgecolors='none')
            ax_tsne.legend(frameon=False)
        elif color_col == "Source Domain":
            for domain in dataset["source_type"].unique():
                mask = dataset["source_type"] == domain
                ax_tsne.scatter(dataset.loc[mask, "tSNE_1"], dataset.loc[mask, "tSNE_2"], label=domain, alpha=0.7, s=20, edgecolors='none')
            ax_tsne.legend(frameon=False, loc='upper right', bbox_to_anchor=(1.2, 1))
        else:
            measure = "emotional_intensity" if color_col == "Emotional Intensity Map" else "transmission_probability"
            sc = ax_tsne.scatter(dataset["tSNE_1"], dataset["tSNE_2"], c=dataset[measure], cmap="plasma", alpha=0.8, s=20, edgecolors='none')
            cbar = plt.colorbar(sc, ax=ax_tsne)
            cbar.outline.set_visible(False)
            cbar.set_label(color_col)

        ax_tsne.set_xlabel("Dimension 1")
        ax_tsne.set_ylabel("Dimension 2")
        ax_tsne.spines['top'].set_visible(False)
        ax_tsne.spines['right'].set_visible(False)
        ax_tsne.grid(alpha=0.1)
        
        st.pyplot(fig_tsne)
