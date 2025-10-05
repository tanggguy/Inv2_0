#!/usr/bin/env python3
"""
Page 4: Analyser une Stratégie en Détail
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from optimization.results_storage import ResultsStorage
from dashboard.components.metrics import (
    display_metric_cards,
    display_detailed_metrics,
    display_parameters_card,
    display_copy_button,
    display_walk_forward_metrics,
    display_performance_badge
)
from dashboard.components.charts import (
    create_heatmap,
    create_distribution_chart,
    create_scatter_plot,
    create_walk_forward_analysis,
    create_parameter_impact_chart
)
from dashboard.utils.session_state import init_session_state

# Configuration
st.set_page_config(
    page_title="Analyze Strategy",
    page_icon="🔬",
    layout="wide"
)

# Initialiser le state
init_session_state()

# Header
st.title("🔬 Analyse Détaillée")
st.markdown("Analyse approfondie d'un run d'optimisation")

st.divider()

# Sélection du run
storage = ResultsStorage()
all_runs = storage.list_runs()

if not all_runs:
    st.info("📭 Aucune optimisation disponible")
    
    if st.button("🚀 Lancer une optimisation", use_container_width=True):
        st.switch_page("pages/1_🚀_Run_Optimization.py")
    
    st.stop()

# Sélecteur de run
col1, col2 = st.columns([3, 1])

with col1:
    # Utiliser le run actif du state ou permettre la sélection
    default_run = st.session_state.get('active_run')
    
    if default_run and default_run in [r['run_id'] for r in all_runs]:
        default_index = [r['run_id'] for r in all_runs].index(default_run)
    else:
        default_index = 0
    
    selected_run_id = st.selectbox(
        "🎯 Sélectionner un run à analyser",
        options=[r['run_id'] for r in all_runs],
        index=default_index,
        format_func=lambda x: f"{x[:50]}... - {next((r['strategy'] for r in all_runs if r['run_id'] == x), 'N/A')}"
    )

with col2:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.rerun()

# Charger le run
run_data = storage.load_run(selected_run_id)

if not run_data:
    st.error(f"❌ Impossible de charger le run: {selected_run_id}")
    st.stop()

summary = run_data['summary']
best = summary.get('best_params', {})
config = run_data['config']

st.divider()

# Informations générales
st.markdown("## 📋 Informations Générales")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**🎯 Stratégie:** {summary.get('strategy', 'N/A')}")
    st.markdown(f"**🔬 Type:** {summary.get('optimization_type', 'N/A').replace('_', ' ').title()}")
    st.markdown(f"**📅 Date:** {summary.get('timestamp', 'N/A')[:19]}")

with col2:
    st.markdown(f"**📈 Symboles:** {', '.join(summary.get('symbols', []))}")
    st.markdown(f"**📆 Période:** {summary.get('period', {}).get('start', 'N/A')} → {summary.get('period', {}).get('end', 'N/A')}")
    st.markdown(f"**🎲 Combinaisons:** {summary.get('total_combinations', 0):,}")

with col3:
    sharpe = best.get('sharpe', 0)
    badge = display_performance_badge(sharpe)
    st.markdown(f"**📊 Performance:** {badge}", unsafe_allow_html=True)
    st.markdown(f"**💰 Capital:** ${config.get('capital', 100000):,}")

st.divider()

# Métriques principales
st.markdown("## 📊 Métriques de Performance")

display_metric_cards({'best': best})
display_detailed_metrics({'best': best})

st.divider()

# Paramètres
col1, col2 = st.columns([2, 1])

with col1:
    display_parameters_card(best)

with col2:
    st.markdown("### 🔗 Actions Rapides")
    
    if st.button("⚖️ Comparer avec d'autres", use_container_width=True):
        st.session_state.selected_runs = [selected_run_id]
        st.switch_page("pages/3_⚖️_Compare_Runs.py")
    
    if st.button("📋 Voir l'historique", use_container_width=True):
        st.switch_page("pages/2_📋_View_History.py")

st.divider()

# Copier les paramètres
st.markdown("### 📋 Copier les Meilleurs Paramètres")
display_copy_button(best)

st.divider()

# Analyse détaillée
st.markdown("## 🔍 Analyse Détaillée")

# Tabs pour différentes analyses
if summary.get('optimization_type') == 'walk_forward':
    tabs = st.tabs(["📊 Walk-Forward", "📈 Distribution", "🔥 Heatmap", "📉 Impact"])
else:
    tabs = st.tabs(["📈 Distribution", "🔥 Heatmap", "📉 Impact", "📊 Scatter"])

# Walk-Forward Analysis (si applicable)
if summary.get('optimization_type') == 'walk_forward':
    with tabs[0]:
        st.markdown("### 🚶 Analyse Walk-Forward")
        
        # Charger les résultats détaillés
        results_df = run_data.get('results_df')
        
        if results_df is not None and not results_df.empty:
            # Créer les données walk-forward
            wf_data = []
            
            # Parser les résultats (cette structure dépend de comment sont stockés les résultats WF)
            # Simuler pour l'exemple
            if 'in_sharpe' in results_df.columns:
                for i, row in results_df.iterrows():
                    wf_data.append({
                        'period': i + 1,
                        'in_sharpe': row.get('in_sharpe', 0),
                        'out_sharpe': row.get('out_sharpe', 0),
                        'degradation': row.get('degradation', 0)
                    })
                
                if wf_data:
                    # Graphique
                    fig = create_walk_forward_analysis(wf_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Métriques
                    display_walk_forward_metrics(wf_data)
            else:
                st.info("💡 Données walk-forward non disponibles en détail")
        else:
            st.info("💡 Résultats détaillés non disponibles")
    
    tab_offset = 1
else:
    tab_offset = 0

# Distribution
with tabs[0 + tab_offset]:
    st.markdown("### 📈 Distribution des Résultats")
    
    results_df = run_data.get('results_df')
    
    if results_df is not None and not results_df.empty:
        
        col1, col2 = st.columns(2)
        
        with col1:
            metric_choice = st.selectbox(
                "Métrique à analyser",
                options=['sharpe', 'return', 'drawdown', 'win_rate'],
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            st.metric(
                f"Médiane {metric_choice.capitalize()}",
                f"{results_df[metric_choice].median():.2f}"
            )
        
        # Graphique de distribution
        fig = create_distribution_chart(results_df, metric_choice)
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        with st.expander("📊 Statistiques détaillées"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Min", f"{results_df[metric_choice].min():.2f}")
            
            with col2:
                st.metric("Max", f"{results_df[metric_choice].max():.2f}")
            
            with col3:
                st.metric("Moyenne", f"{results_df[metric_choice].mean():.2f}")
            
            with col4:
                st.metric("Écart-type", f"{results_df[metric_choice].std():.2f}")
    else:
        st.info("💡 Résultats détaillés non disponibles")

# Heatmap
with tabs[1 + tab_offset]:
    st.markdown("### 🔥 Heatmap des Paramètres")
    
    results_df = run_data.get('results_df')
    
    if results_df is not None and not results_df.empty:
        
        # Identifier les paramètres disponibles
        exclude_cols = ['sharpe', 'return', 'drawdown', 'trades', 'win_rate', 'avg_win', 'avg_loss']
        param_cols = [col for col in results_df.columns if col not in exclude_cols]
        
        if len(param_cols) >= 2:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                x_param = st.selectbox("Paramètre X", param_cols, index=0)
            
            with col2:
                y_param = st.selectbox("Paramètre Y", param_cols, index=1 if len(param_cols) > 1 else 0)
            
            with col3:
                metric = st.selectbox(
                    "Métrique",
                    options=['sharpe', 'return', 'drawdown', 'win_rate'],
                    format_func=lambda x: x.capitalize()
                )
            
            # Créer la heatmap
            fig = create_heatmap(results_df, x_param, y_param, metric)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Pas assez de paramètres pour créer une heatmap (minimum 2)")
    else:
        st.info("💡 Résultats détaillés non disponibles")

# Impact des paramètres
with tabs[2 + tab_offset]:
    st.markdown("### 📉 Impact des Paramètres")
    
    results_df = run_data.get('results_df')
    
    if results_df is not None and not results_df.empty:
        
        exclude_cols = ['sharpe', 'return', 'drawdown', 'trades', 'win_rate', 'avg_win', 'avg_loss']
        param_cols = [col for col in results_df.columns if col not in exclude_cols]
        
        if param_cols:
            col1, col2 = st.columns(2)
            
            with col1:
                param = st.selectbox("Paramètre à analyser", param_cols)
            
            with col2:
                metric = st.selectbox(
                    "Impact sur",
                    options=['sharpe', 'return', 'drawdown', 'win_rate'],
                    format_func=lambda x: x.capitalize(),
                    key='impact_metric'
                )
            
            # Graphique d'impact
            fig = create_parameter_impact_chart(results_df, param, metric)
            st.plotly_chart(fig, use_container_width=True)
            
            # Analyse
            grouped = results_df.groupby(param)[metric].agg(['mean', 'std', 'count'])
            best_value = grouped['mean'].idxmax()
            
            st.success(f"✨ Meilleure valeur pour {param}: **{best_value}** (moyenne {metric}: {grouped.loc[best_value, 'mean']:.2f})")
        else:
            st.info("💡 Aucun paramètre variable détecté")
    else:
        st.info("💡 Résultats détaillés non disponibles")

# Scatter plot (uniquement si pas walk-forward)
if summary.get('optimization_type') != 'walk_forward':
    with tabs[3]:
        st.markdown("### 📊 Scatter Plot")
        
        results_df = run_data.get('results_df')
        
        if results_df is not None and not results_df.empty:
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                x_metric = st.selectbox("Axe X", ['return', 'sharpe', 'drawdown', 'win_rate'])
            
            with col2:
                y_metric = st.selectbox("Axe Y", ['sharpe', 'return', 'drawdown', 'win_rate'])
            
            with col3:
                # Option de couleur
                exclude_cols = ['sharpe', 'return', 'drawdown', 'trades', 'win_rate', 'avg_win', 'avg_loss']
                param_cols = [col for col in results_df.columns if col not in exclude_cols]
                
                color_by = st.selectbox(
                    "Couleur par",
                    options=[None] + param_cols,
                    format_func=lambda x: "Aucun" if x is None else x
                )
            
            # Créer le scatter plot
            fig = create_scatter_plot(results_df, x_metric, y_metric, color_by)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Résultats détaillés non disponibles")