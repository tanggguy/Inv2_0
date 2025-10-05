#!/usr/bin/env python3
"""
Composants de métriques pour le dashboard
"""

import streamlit as st
from typing import Dict, Optional


def display_metric_cards(results: Dict):
    """
    Affiche les cartes de métriques principales
    
    Args:
        results: Dictionnaire de résultats
    """
    best = results.get('best', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sharpe = best.get('sharpe', 0)
        color = "normal" if sharpe > 1 else "off"
        st.metric(
            label="📊 Sharpe Ratio",
            value=f"{sharpe:.2f}",
            delta=None,
            delta_color=color
        )
    
    with col2:
        return_pct = best.get('return', 0)
        color = "normal" if return_pct > 0 else "inverse"
        st.metric(
            label="💰 Rendement Total",
            value=f"{return_pct:.2f}%",
            delta=None,
            delta_color=color
        )
    
    with col3:
        drawdown = best.get('drawdown', 0)
        st.metric(
            label="📉 Max Drawdown",
            value=f"{abs(drawdown):.2f}%",
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        trades = best.get('trades', 0)
        st.metric(
            label="🔄 Nombre de Trades",
            value=f"{trades}",
            delta=None
        )


def display_detailed_metrics(results: Dict):
    """
    Affiche des métriques détaillées dans un expander
    
    Args:
        results: Dictionnaire de résultats
    """
    best = results.get('best', {})
    
    with st.expander("📋 Voir plus de métriques", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("✅ Win Rate", f"{best.get('win_rate', 0):.2f}%")
            st.metric("📈 Avg Win", f"${best.get('avg_win', 0):.2f}")
        
        with col2:
            st.metric("❌ Loss Rate", f"{100 - best.get('win_rate', 0):.2f}%")
            st.metric("📉 Avg Loss", f"${abs(best.get('avg_loss', 0)):.2f}")
        
        with col3:
            avg_win = abs(best.get('avg_win', 1))
            avg_loss = abs(best.get('avg_loss', 1))
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            st.metric("⚖️ Profit Factor", f"{profit_factor:.2f}")
            st.metric("🎯 Total Combos", f"{results.get('total_combinations', 0):,}")


def display_parameters_card(params: Dict):
    """
    Affiche une carte avec les paramètres
    
    Args:
        params: Dictionnaire de paramètres
    """
    st.markdown("### 🎯 Meilleurs Paramètres")
    
    # Filtrer les paramètres (enlever les métriques)
    exclude_keys = ['sharpe', 'return', 'drawdown', 'trades', 'win_rate', 'avg_win', 'avg_loss']
    clean_params = {k: v for k, v in params.items() if k not in exclude_keys}
    
    if clean_params:
        # Afficher en colonnes
        num_cols = min(3, len(clean_params))
        cols = st.columns(num_cols)
        
        for i, (key, value) in enumerate(clean_params.items()):
            with cols[i % num_cols]:
                # Formater le nom du paramètre
                display_name = key.replace('_', ' ').title()
                st.markdown(f"**{display_name}**")
                st.code(str(value))
    else:
        st.info("Aucun paramètre à afficher")


def display_copy_button(params: Dict):
    """
    Affiche un bouton pour copier les paramètres
    
    Args:
        params: Dictionnaire de paramètres
    """
    # Filtrer les paramètres
    exclude_keys = ['sharpe', 'return', 'drawdown', 'trades', 'win_rate', 'avg_win', 'avg_loss']
    clean_params = {k: v for k, v in params.items() if k not in exclude_keys}
    
    if clean_params:
        # Créer le code Python à copier
        params_str = "params = {\n"
        for key, value in clean_params.items():
            if isinstance(value, str):
                params_str += f"    '{key}': '{value}',\n"
            else:
                params_str += f"    '{key}': {value},\n"
        params_str += "}"
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.code(params_str, language='python')
        
        with col2:
            if st.button("📋 Copier", use_container_width=True):
                st.toast("✅ Paramètres copiés !", icon="✅")
                # Note: Le vrai copy to clipboard nécessite du JS custom
                st.session_state['copied_params'] = params_str


def display_performance_badge(sharpe: float) -> str:
    """
    Retourne un badge de performance
    
    Args:
        sharpe: Sharpe ratio
    
    Returns:
        Badge HTML
    """
    if sharpe > 2:
        badge = '<span style="background-color: #10b981; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold;">⭐⭐⭐⭐⭐ EXCELLENT</span>'
    elif sharpe > 1.5:
        badge = '<span style="background-color: #3b82f6; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold;">⭐⭐⭐⭐ TRÈS BON</span>'
    elif sharpe > 1:
        badge = '<span style="background-color: #8b5cf6; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold;">⭐⭐⭐ BON</span>'
    elif sharpe > 0.5:
        badge = '<span style="background-color: #f59e0b; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold;">⭐⭐ ACCEPTABLE</span>'
    else:
        badge = '<span style="background-color: #ef4444; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold;">⭐ FAIBLE</span>'
    
    return badge


def display_walk_forward_metrics(wf_results: list):
    """
    Affiche les métriques Walk-Forward
    
    Args:
        wf_results: Liste des résultats walk-forward
    """
    if not wf_results:
        return
    
    import pandas as pd
    df = pd.DataFrame(wf_results)
    
    st.markdown("### 📊 Analyse Walk-Forward")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_in = df['in_sharpe'].mean()
        st.metric("📈 Avg In-Sample Sharpe", f"{avg_in:.2f}")
    
    with col2:
        avg_out = df['out_sharpe'].mean()
        st.metric("📉 Avg Out-Sample Sharpe", f"{avg_out:.2f}")
    
    with col3:
        avg_deg = df['degradation'].mean()
        color = "normal" if avg_deg < 0.3 else "inverse"
        st.metric("⚠️ Dégradation Moyenne", f"{avg_deg:.2f}", delta_color=color)
    
    # Évaluation
    if avg_deg < 0.3:
        st.success("✅ EXCELLENT - Stratégie robuste, faible overfitting")
    elif avg_deg < 0.5:
        st.info("✔️ BON - Dégradation acceptable")
    else:
        st.warning("⚠️ ATTENTION - Overfitting potentiel détecté")