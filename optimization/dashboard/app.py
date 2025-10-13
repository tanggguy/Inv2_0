#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    TRADING SYSTEM DASHBOARD - Page d'accueil
═══════════════════════════════════════════════════════════════════════════════

Dashboard principal pour l'optimisation et l'analyse des stratégies de trading
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from optimization.results_storage import ResultsStorage

# Configuration de la page
st.set_page_config(
    page_title="Trading System Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS personnalisé pour dark mode
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def main():
    """Page d'accueil principale"""

    # Header
    st.markdown(
        '<h1 class="main-header">🚀 Trading System Dashboard</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 3rem; color: #888;'>
            Optimisation et analyse avancée de stratégies de trading algorithmique
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Statistiques globales
    st.markdown("## 📊 Vue d'ensemble")

    storage = ResultsStorage()
    stats = storage.get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🔬 Total Optimisations", value=stats.get("total_runs", 0), delta=None
        )

    with col2:
        st.metric(
            label="📈 Meilleur Sharpe",
            value=f"{stats.get('best_sharpe', 0):.2f}",
            delta=None,
        )

    with col3:
        st.metric(
            label="💰 Meilleur Return",
            value=f"{stats.get('best_return', 0):.1f}%",
            delta=None,
        )

    with col4:
        st.metric(
            label="🎯 Stratégies Testées",
            value=stats.get("total_strategies", 0),
            delta=None,
        )

    st.divider()

    # Guide de navigation
    st.markdown("## 🧭 Navigation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        ### 🚀 Lancer une Optimisation
        - Choisir une stratégie
        - Sélectionner un preset ou personnaliser
        - Grid Search ou Walk-Forward
        - Suivre la progression en temps réel
        
        👉 **Allez à la page "Run Optimization"**
        """
        )

        st.markdown(
            """
        ### ⚖️ Comparer des Runs
        - Sélectionner 2+ optimisations
        - Tableaux comparatifs
        - Graphiques equity curves
        - Analyse côte à côte
        
        👉 **Allez à la page "Compare Runs"**
        """
        )

    with col2:
        st.markdown(
            """
        ### 📋 Consulter l'Historique
        - Liste de tous les runs
        - Filtrage avancé
        - Tri par métriques
        - Export et suppression
        
        👉 **Allez à la page "View History"**
        """
        )

        st.markdown(
            """
        ### 🔬 Analyser en Détail
        - Détails d'un run spécifique
        - Walk-Forward analysis
        - Heatmaps de paramètres
        - Distribution des résultats
        
        👉 **Allez à la page "Analyze Strategy"**
        """
        )

    st.divider()

    # Dernières optimisations
    st.markdown("## 🕒 Dernières Optimisations")

    recent_runs = storage.list_runs()[-5:][::-1]  # 5 derniers, ordre inverse

    if recent_runs:
        for run in recent_runs:
            with st.expander(f"📌 {run['run_id']} - {run['strategy']}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Type:** {run['type']}")
                    st.write(f"**Symboles:** {', '.join(run['symbols'])}")

                with col2:
                    st.write(f"**Sharpe:** {run['best_sharpe']:.2f}")
                    st.write(f"**Return:** {run['best_return']:.2f}%")

                with col3:
                    st.write(f"**Combinaisons:** {run['total_combos']}")
                    st.write(f"**Date:** {run['timestamp'][:10]}")
    else:
        st.info("Aucune optimisation pour le moment. Lancez-en une !")

    st.divider()

    # Quick actions
    st.markdown("## ⚡ Actions Rapides")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Nouvelle Optimisation", use_container_width=True):
            st.switch_page("pages/1_🚀_Run_Optimization.py")

    with col2:
        if st.button("📋 Voir l'Historique", use_container_width=True):
            st.switch_page("pages/2_📋_View_History.py")

    with col3:
        if st.button("⚖️ Comparer des Runs", use_container_width=True):
            st.switch_page("pages/3_⚖️_Compare_Runs.py")

    # Footer
    st.markdown(
        """
        ---
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📊 Trading System Dashboard v1.0 | Powered by Streamlit & Backtrader
        </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
