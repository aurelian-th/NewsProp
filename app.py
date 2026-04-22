import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
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
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from simulation.phase45 import (
        SimulationConfig, compute_news_features, load_and_normalize_datasets,
        run_single_simulation, build_population_graph
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
    real = Path("scraper/real/stirimd_dataset.json")
    fake = Path("scraper/fake/stopfals_final_dataset.json")
    tg = Path("scraper/telegram/moldova_news_50.json")

    normalized = load_and_normalize_datasets(fake, real, tg)
    return compute_news_features(normalized)

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
    df_tsne["hover_text"] = df_tsne["headline"].apply(lambda x: x[:60] + "...")
    df_tsne["Class"] = df_tsne["is_fake"].map({True: "Disinformation", False: "Verified"})
    return df_tsne

col1, col2 = st.columns([3, 1])
with col1:
    st.title("NewsProp Analytics & Simulation System")
with col2:
    st.markdown("<div style='text-align:right; margin-top:20px;'><span style='color:gray'>Moldovan Digital Epidemic Tracker</span></div>", unsafe_allow_html=True)
st.markdown("---")

try:
    with st.spinner("Initializing system constraints..."):
        dataset = load_data()
        dataset = get_tsne_clusters(dataset)
except Exception as e:
    st.error(f"System Error: {e}")
    st.stop()

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
        st.warning("No entities found.")
        st.stop()

    article_idx = st.sidebar.selectbox("Select Origin Entity", matches.index, format_func=lambda x: f"[{'Disinfo' if matches.loc[x, 'is_fake'] else 'Verified'}] {matches.loc[x, 'headline'][:40]}...")
    article = matches.loc[article_idx].to_dict()
else:
    custom_title = st.text_input("Payload Title", "National infrastructure failure reports spreading in major hubs")
    custom_desc = st.text_area("Content Payload (NLP Analyzed)", "Scientists and experts warn...")
    is_fake = st.checkbox("Flag as Disinformation?", value=True)
    if not custom_title:
        st.stop()
        
    custom_df = pd.DataFrame([{
        "headline": custom_title, "combined_text": f"{custom_title} {custom_desc}",
        "is_fake": is_fake, "source": "Synthetic_Injection", "source_type": "fake" if is_fake else "real",
        "views": dataset["views"].median(), "likes": dataset["likes"].median(), "shares": dataset["shares"].median(),
        "comments": dataset["comments"].median(), "top_comment_count": dataset["top_comment_count"].median(),
        "has_debunk_context": not is_fake
    }])
    with st.spinner("Running NLP embedding vectors..."):
        article = compute_news_features(custom_df).iloc[0].to_dict()

st.sidebar.markdown("---")
st.sidebar.subheader("Topological Parameters")
num_agents = st.sidebar.number_input("Population Size", min_value=100, max_value=5000, value=500, step=100)
ticks = st.sidebar.number_input("Epoch Duration", min_value=10, max_value=200, value=75, step=10)

st.sidebar.markdown("---")
st.sidebar.subheader("Defense Matrix (Intervention)")
intervene = st.sidebar.checkbox("Compute Pre-bunking Delta?", value=True, help="Runs baseline and intervention side-by-side to show metrics.")
hub_percent = st.sidebar.slider("Hub Immunization Coverage (%)", 1, 20, 5) / 100.0 if intervene else 0.05

tab_sim, tab_data = st.tabs(["[Module 1] Propagation Dynamics", "[Module 2] Latent Clustering (t-SNE)"])

with tab_sim:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Classification", "Disinformation" if article["is_fake"] else "Verified")
    c2.metric("Domain Node", article["source"])
    c3.metric("Emotional Coefficient", f"{article['emotional_intensity']:.3f}")
    c4.metric("Base Spread Vector (Beta)", f"{article['transmission_probability']:.3f}")
    st.markdown(f"**Payload Fragment:** {article['headline']}")
    
    if st.button("? Execute Propagation Models", type="primary", use_container_width=True):
        with st.spinner("Compiling synthetic graph and executing multi-scenario mathematical simulations..."):
            rng = np.random.default_rng(42)
            cfg = SimulationConfig(num_agents=num_agents, attach_edges=3, ticks=ticks, runs=1, initial_infected=max(1, int(num_agents * 0.01)), hub_percent=hub_percent, random_seed=42)
            graph, agents, hubs = build_population_graph(config=cfg, rng=rng)
            
            # Baseline
            tl_base, final_state_base = run_single_simulation(graph, agents.copy(), article, cfg, np.random.default_rng(42), False, set())
            
            if intervene:
                tl_int, final_state_int = run_single_simulation(graph, agents.copy(), article, cfg, np.random.default_rng(42), True, hubs)
                peak_base = tl_base['I'].max()
                peak_int = tl_int['I'].max()
                saved_pct = ((peak_base - peak_int) / peak_base * 100) if peak_base > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Baseline Peak Infections", int(peak_base))
                m2.metric("Intervention Peak Infections", int(peak_int), delta=f"{-int(peak_base - peak_int)}")
                m3.metric("Network Saved (Delta)", f"{saved_pct:.1f}%", delta=f"{saved_pct:.1f}x efficiency")
                st.divider()

            g1, g2 = st.columns(2)
            
            with g1:
                st.subheader("SEIZ Infection Curves", divider="gray")
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(x=tl_base["tick"], y=tl_base["S"], name="Susceptible", line=dict(color="#9e9e9e")))
                fig_timeline.add_trace(go.Scatter(x=tl_base["tick"], y=tl_base["E"], name="Exposed", line=dict(color="#fb8c00")))
                fig_timeline.add_trace(go.Scatter(x=tl_base["tick"], y=tl_base["I"], name="Infected (Baseline)", line=dict(color="#e53935", width=3)))
                fig_timeline.add_trace(go.Scatter(x=tl_base["tick"], y=tl_base["Z"], name="Skeptic (Firewall)", line=dict(color="#43a047")))
                
                if intervene:
                    fig_timeline.add_trace(go.Scatter(x=tl_int["tick"], y=tl_int["I"], name="Infected (Intervention)", line=dict(color="#e0218a", dash="dot", width=3)))
                
                fig_timeline.update_layout(
                    template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Epoch / Time", yaxis_title="Node Count", margin=dict(l=0, r=0, t=30, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

                st.subheader("Data Export Actions", divider="gray")
                export_df = pd.concat([tl_base.assign(Scenario='Baseline')], ignore_index=True)
                if intervene:
                    export_df = pd.concat([export_df, tl_int.assign(Scenario='Intervention')], ignore_index=True)
                csv = export_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Raw Trajectory CSV (For Research Paper)", csv, "seiz_simulation_results.csv", "text/csv", use_container_width=True)

            with g2:
                st.subheader("Topological Inspection (Interactive)", divider="gray")
                pos = nx.spring_layout(graph, seed=42)
                
                # Interactive Graph via Plotly
                edge_x, edge_y = [], []
                for edge in graph.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                node_x = [pos[node][0] for node in graph.nodes()]
                node_y = [pos[node][1] for node in graph.nodes()]
                state_refs = [int(final_state_base[node]) for node in graph.nodes()]
                colors = [{"0": "#9e9e9e", "1": "#fb8c00", "2": "#e53935", "3": "#43a047"}[str(s)] for s in state_refs]
                names = [{"0": "Susceptible", "1": "Exposed", "2": "Infected", "3": "Skeptic Firewall"}[str(s)] for s in state_refs]
                
                is_hub = ["⭐ Hub Node" if n in hubs else "Standard Node" for n in graph.nodes()]

                fig_net = go.Figure()
                fig_net.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#444'), hoverinfo='none', mode='lines'))
                fig_net.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers', hoverinfo='text',
                    marker=dict(showscale=False, color=colors, size=[12 if n in hubs else 6 for n in graph.nodes()], line_width=0),
                    text=[f"Node: {i}<br>State: {state}<br>{hub}" for i, state, hub in zip(graph.nodes(), names, is_hub)]))
                fig_net.update_layout(
                    showlegend=False, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_net, use_container_width=True)

with tab_data:
    st.subheader("Global Information Environment State (Interactive t-SNE)", divider="gray")
    opt_col, _ = st.columns([1, 2])
    with opt_col:
        color_col = st.selectbox("Display Overlay Layer:", ["Classification", "Source Domain", "Emotional Intensity Map", "Transmission Velocity Map"])

    color_mapping = "Class"
    cmap = None
    if color_col == "Source Domain": color_mapping = "source_type"
    elif color_col == "Emotional Intensity Map": color_mapping, cmap = "emotional_intensity", "plasma"
    elif color_col == "Transmission Velocity Map": color_mapping, cmap = "transmission_probability", "inferno"

    fig_tsne = px.scatter(
        dataset, x="tSNE_1", y="tSNE_2", color=color_mapping,
        hover_name="hover_text", hover_data=["source", "is_fake", "views", "shares"],
        color_continuous_scale=cmap, color_discrete_map={"Disinformation": "#e53935", "Verified": "#1e88e5"}
    )
    fig_tsne.update_layout(
        template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0), legend_title_text=''
    )
    st.plotly_chart(fig_tsne, use_container_width=True)
    
    st.download_button("Download Clustering Coordinates & Features (CSV)", dataset.to_csv(index=False).encode('utf-8'), "tsne_dataset_extract.csv", "text/csv")
