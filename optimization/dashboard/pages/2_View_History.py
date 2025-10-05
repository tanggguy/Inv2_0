#!/usr/bin/env python3
"""
Page 2: Consulter l'Historique
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from optimization.results_storage import ResultsStorage
from dashboard.components.results_table import (
    display_runs_table, 
    create_filterable_table,
    display_detailed_results_table
)
from dashboard.utils.session_state import init_session_state

# Configuration
st.set_page_config(
    page_title="View History",
    page_icon="📋",
    layout="wide"
)

# Initialiser le state
init_session_state()

# Header
st.title("📋 Historique des Optimisations")
st.markdown("Consultez, filtrez et gérez tous vos runs d'optimisation")

st.divider()

# Charger les données
storage = ResultsStorage()
all_runs = storage.list_runs()

if not all_runs:
    st.info("📭 Aucune optimisation dans l'historique. Lancez-en une !")
    
    if st.button("🚀 Lancer une optimisation", use_container_width=True):
        st.switch_page("pages/1_🚀_Run_Optimization.py")
    
    st.stop()

# Statistiques rapides
st.markdown("## 📊 Statistiques Globales")

stats = storage.get_statistics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🔬 Total Runs", stats['total_runs'])

with col2:
    st.metric("📈 Meilleur Sharpe", f"{stats['best_sharpe']:.2f}")

with col3:
    st.metric("💰 Meilleur Return", f"{stats['best_return']:.1f}%")

with col4:
    st.metric("🎯 Stratégies", stats['total_strategies'])

st.divider()

# Filtres
st.markdown("## 🔍 Filtrer les Runs")

filtered_df = create_filterable_table(all_runs)

if filtered_df.empty:
    st.warning("Aucun run ne correspond aux filtres")
    st.stop()

st.divider()

# Tableau principal
st.markdown("## 📊 Tableau des Runs")

# Options d'affichage
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"**{len(filtered_df)} runs affichés**")

with col2:
    view_mode = st.radio(
        "Vue",
        options=['Compacte', 'Détaillée'],
        horizontal=True,
        label_visibility="collapsed"
    )

# Afficher le tableau
display_runs_table(
    filtered_df.to_dict('records'),
    selectable=False,
    show_actions=True
)

st.divider()

# Section des meilleurs runs
st.markdown("## 🏆 Top Performances")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Meilleur Sharpe Ratio")
    
    top_sharpe = filtered_df.nlargest(5, 'best_sharpe')
    
    for i, row in top_sharpe.iterrows():
        with st.container():
            col_a, col_b, col_c = st.columns([2, 1, 1])
            
            with col_a:
                st.markdown(f"**{row['strategy']}**")
                st.caption(f"{row['run_id'][:30]}...")
            
            with col_b:
                st.metric("Sharpe", f"{row['best_sharpe']:.2f}")
            
            with col_c:
                if st.button("🔬", key=f"analyze_sharpe_{i}", help="Analyser"):
                    st.session_state.active_run = row['run_id']
                    st.switch_page("pages/4_🔬_Analyze_Strategy.py")

with col2:
    st.markdown("### 💰 Meilleur Rendement")
    
    top_return = filtered_df.nlargest(5, 'best_return')
    
    for i, row in top_return.iterrows():
        with st.container():
            col_a, col_b, col_c = st.columns([2, 1, 1])
            
            with col_a:
                st.markdown(f"**{row['strategy']}**")
                st.caption(f"{row['run_id'][:30]}...")
            
            with col_b:
                st.metric("Return", f"{row['best_return']:.2f}%")
            
            with col_c:
                if st.button("🔬", key=f"analyze_return_{i}", help="Analyser"):
                    st.session_state.active_run = row['run_id']
                    st.switch_page("pages/4_🔬_Analyze_Strategy.py")

st.divider()

# Export et gestion
st.markdown("## ⚙️ Gestion")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📤 Export")
    
    # Préparer le CSV
    export_df = filtered_df.copy()
    csv = export_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Télécharger CSV",
        data=csv,
        file_name=f"optimization_history_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    st.markdown("### 🔄 Rafraîchir")
    
    if st.button("🔄 Actualiser les données", use_container_width=True):
        st.rerun()

with col3:
    st.markdown("### 🗑️ Nettoyage")
    
    with st.popover("🗑️ Supprimer des runs", use_container_width=True):
        st.warning("⚠️ Action irréversible")
        
        # Sélection des runs à supprimer
        runs_to_delete = st.multiselect(
            "Sélectionner les runs à supprimer",
            options=[r['run_id'] for r in all_runs],
            format_func=lambda x: x[:40] + '...'
        )
        
        if runs_to_delete:
            if st.button(f"🗑️ Supprimer {len(runs_to_delete)} run(s)", type="primary"):
                for run_id in runs_to_delete:
                    storage.delete_run(run_id)
                
                st.success(f"✅ {len(runs_to_delete)} run(s) supprimé(s)")
                st.rerun()

# Instructions
with st.expander("💡 Aide"):
    st.markdown("""
    ### Utilisation de l'historique
    
    **Filtres disponibles:**
    - 🎯 Par stratégie
    - 🔬 Par type d'optimisation
    - 📈 Par Sharpe minimum
    
    **Actions sur un run:**
    - 🔬 **Analyser**: Voir l'analyse détaillée
    - 🗑️ **Supprimer**: Retirer de l'historique
    
    **Export:**
    - 📥 Télécharger l'historique en CSV
    
    **Tri:**
    - Cliquez sur les en-têtes de colonnes pour trier
    """)