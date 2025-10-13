#!/usr/bin/env python3
"""
Page 3: Comparer des Runs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from optimization.results_storage import ResultsStorage
from dashboard.components.results_table import (
    display_comparison_table,
    display_parameters_comparison,
)
from dashboard.components.charts import create_comparison_chart, create_scatter_plot
from dashboard.components.metrics import display_performance_badge
from dashboard.utils.session_state import init_session_state

# Configuration
st.set_page_config(page_title="Compare Runs", page_icon="⚖️", layout="wide")

# Initialiser le state
init_session_state()

# Header
st.title("⚖️ Comparer des Runs")
st.markdown("Comparez plusieurs optimisations côte à côte")

st.divider()

# Charger les données
storage = ResultsStorage()
all_runs = storage.list_runs()

if not all_runs:
    st.info("📭 Aucune optimisation disponible pour comparaison")

    if st.button("🚀 Lancer une optimisation", use_container_width=True):
        st.switch_page("pages/1_🚀_Run_Optimization.py")

    st.stop()

# Sélection des runs à comparer
st.markdown("## 🎯 Sélection des Runs")

col1, col2 = st.columns([3, 1])

with col1:
    # Multiselect pour choisir les runs
    selected_run_ids = st.multiselect(
        "Sélectionner 2 à 5 runs à comparer",
        options=[r["run_id"] for r in all_runs],
        format_func=lambda x: f"{x[:50]}... - {next((r['strategy'] for r in all_runs if r['run_id'] == x), 'N/A')}",
        max_selections=5,
        help="Sélectionnez entre 2 et 5 runs pour la comparaison",
    )

with col2:
    # Filtres rapides
    st.markdown("**Filtres rapides**")

    if st.button("🏆 Top 3 Sharpe", use_container_width=True):
        top_runs = sorted(
            all_runs, key=lambda x: x.get("best_sharpe", 0), reverse=True
        )[:3]
        selected_run_ids = [r["run_id"] for r in top_runs]
        st.rerun()

    if st.button("💰 Top 3 Return", use_container_width=True):
        top_runs = sorted(
            all_runs, key=lambda x: x.get("best_return", 0), reverse=True
        )[:3]
        selected_run_ids = [r["run_id"] for r in top_runs]
        st.rerun()

# Vérifier la sélection
if not selected_run_ids:
    st.info("👆 Sélectionnez au moins 2 runs pour commencer la comparaison")
    st.stop()

if len(selected_run_ids) < 2:
    st.warning("⚠️ Veuillez sélectionner au moins 2 runs")
    st.stop()

# Charger les données des runs sélectionnés
runs_data = {}

for run_id in selected_run_ids:
    data = storage.load_run(run_id)
    if data:
        runs_data[run_id] = data

if not runs_data:
    st.error("❌ Impossible de charger les runs sélectionnés")
    st.stop()

st.divider()

# Comparaison des métriques
st.markdown("## 📊 Comparaison des Métriques")

# Tableau comparatif
display_comparison_table(runs_data)

st.divider()

# Graphiques de comparaison
st.markdown("## 📈 Visualisations Comparatives")

tab1, tab2, tab3 = st.tabs(["📊 Métriques", "🎯 Paramètres", "📈 Performance"])

with tab1:
    st.markdown("### 📊 Comparaison des Métriques Clés")

    # Préparer les données pour visualisation
    comparison_data = []

    for run_id, data in runs_data.items():
        best = data["summary"].get("best_params", {})
        comparison_data.append(
            {
                "Run": run_id[:20] + "...",
                "Sharpe": best.get("sharpe", 0),
                "Return": best.get("return", 0),
                "Drawdown": abs(best.get("drawdown", 0)),
                "Win Rate": best.get("win_rate", 0),
            }
        )

    df_comp = pd.DataFrame(comparison_data)

    # Graphique Sharpe vs Return
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Sharpe Ratio")
        st.bar_chart(df_comp.set_index("Run")["Sharpe"])

    with col2:
        st.markdown("#### Rendement Total (%)")
        st.bar_chart(df_comp.set_index("Run")["Return"])

    # Scatter plot
    st.markdown("#### 📍 Return vs Drawdown")

    import plotly.graph_objects as go

    fig = go.Figure()

    for i, row in df_comp.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["Drawdown"]],
                y=[row["Return"]],
                mode="markers+text",
                name=row["Run"],
                text=[row["Run"]],
                textposition="top center",
                marker=dict(size=15),
            )
        )

    fig.update_layout(
        xaxis_title="Max Drawdown (%)",
        yaxis_title="Return (%)",
        template="plotly_dark",
        height=400,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 🎯 Comparaison des Paramètres")

    display_parameters_comparison(runs_data)

    # Analyse des différences
    st.markdown("#### 🔍 Analyse des Différences")

    # Extraire tous les paramètres
    all_params = {}
    exclude_keys = [
        "sharpe",
        "return",
        "drawdown",
        "trades",
        "win_rate",
        "avg_win",
        "avg_loss",
    ]

    for run_id, data in runs_data.items():
        best = data["summary"].get("best_params", {})
        params = {k: v for k, v in best.items() if k not in exclude_keys}
        all_params[run_id[:20]] = params

    # Identifier les paramètres qui varient
    varying_params = set()

    if all_params:
        first_params = next(iter(all_params.values()))
        for param in first_params.keys():
            values = [p.get(param) for p in all_params.values()]
            if len(set(values)) > 1:
                varying_params.add(param)

    if varying_params:
        st.info(f"🔄 Paramètres qui varient: {', '.join(varying_params)}")
    else:
        st.success("✅ Tous les runs utilisent les mêmes paramètres")

with tab3:
    st.markdown("### 📈 Analyse de Performance")

    # Calculer des scores
    scores_data = []

    for run_id, data in runs_data.items():
        best = data["summary"].get("best_params", {})

        # Score composite
        sharpe = best.get("sharpe", 0) or 0
        return_pct = best.get("return", 0) or 0
        drawdown = abs(best.get("drawdown", 0)) or 0
        win_rate = best.get("win_rate", 0) or 0

        # Score pondéré
        score = (
            sharpe * 0.3
            + (return_pct / 100) * 0.3
            + (1 - drawdown / 100) * 0.2
            + (win_rate / 100) * 0.2
        )

        scores_data.append(
            {
                "Run": run_id[:20] + "...",
                "Score": score,
                "Sharpe": sharpe,
                "Badge": display_performance_badge(sharpe),
            }
        )

    df_scores = pd.DataFrame(scores_data)
    df_scores = df_scores.sort_values("Score", ascending=False)

    # Afficher le classement
    st.markdown("#### 🏆 Classement Global")

    for i, row in df_scores.iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            rank = list(df_scores.index).index(i) + 1
            medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"{rank}."
            st.markdown(f"{medal} **{row['Run']}**")

        with col2:
            st.markdown(f"Score: **{row['Score']:.2f}**")

        with col3:
            st.markdown(row["Badge"], unsafe_allow_html=True)

    # Recommandation
    st.divider()

    best_run = df_scores.iloc[0]

    st.success(
        f"🎯 **Recommandation:** Le run **{best_run['Run']}** obtient le meilleur score global ({best_run['Score']:.2f})"
    )

st.divider()

# Actions rapides
st.markdown("## ⚡ Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔬 Analyser le meilleur", use_container_width=True):
        best_run_id = df_scores.iloc[0]["Run"]
        # Retrouver le run_id complet
        full_id = next(
            (r["run_id"] for r in all_runs if r["run_id"].startswith(best_run_id[:20])),
            None,
        )
        if full_id:
            st.session_state.active_run = full_id
            st.switch_page("pages/4_🔬_Analyze_Strategy.py")

with col2:
    if st.button("📋 Exporter la comparaison", use_container_width=True):
        # Créer un CSV de comparaison
        csv = df_comp.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger",
            data=csv,
            file_name=f"comparison_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

with col3:
    if st.button("🔄 Nouvelle comparaison", use_container_width=True):
        st.rerun()
