"""
Composants pour adaptation des paramètres par stratégie
"""
import streamlit as st
from optimization.optimization_config import OptimizationConfig


def load_strategy_params(strategy_name: str, preset_config: dict = None) -> dict:
    """
    Charge les paramètres par défaut pour une stratégie
    
    Args:
        strategy_name: Nom de la stratégie
        preset_config: Config du preset (optionnel, prioritaire)
    
    Returns:
        Dict param_grid
    """
    # Priorité au preset si fourni
    if preset_config and 'param_grid' in preset_config:
        return preset_config['param_grid']
    
    # Charger les defaults de la stratégie
    config_manager = OptimizationConfig()
    defaults = config_manager.get_strategy_defaults(strategy_name)
    
    if defaults and 'param_grid' in defaults:
        return defaults['param_grid']
    
    # Fallback
    st.warning(f"⚠️ Pas de paramètres par défaut pour '{strategy_name}'")
    return {
        'ma_period': [10, 20, 30],
        'rsi_period': [7, 14, 21]
    }


def get_strategy_info(strategy_name: str) -> dict:
    """Retourne les infos d'une stratégie"""
    
    info_map = {
        'MovingAverage': {
            'description': 'Croisement de moyennes mobiles',
            'type': 'Trend Following',
            'difficulty': '⭐ Facile'
        },
        'RSI': {
            'description': 'RSI avec seuils',
            'type': 'Oscillateur',
            'difficulty': '⭐ Facile'
        },
        'MaSuperStrategie': {
            'description': 'Stratégie personnalisée avec stops',
            'type': 'Custom',
            'difficulty': '⭐⭐ Moyen'
        }
    }
    
    return info_map.get(strategy_name, {
        'description': 'Stratégie personnalisée',
        'type': 'Custom',
        'difficulty': '⭐⭐ Moyen'
    })


def render_param_editor(strategy_name: str, preset_config: dict = None) -> dict:
    """
    Affiche un éditeur de paramètres adapté
    
    Args:
        strategy_name: Nom de la stratégie
        preset_config: Config du preset
    
    Returns:
        param_grid modifié
    """
    st.subheader("📊 Grille de Paramètres")
    
    # Charger les paramètres
    param_grid = load_strategy_params(strategy_name, preset_config)
    
    # Afficher
    with st.expander("👀 Paramètres chargés", expanded=True):
        st.json(param_grid)
    
    # Calculer combinaisons
    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    
    st.metric("Combinaisons totales", f"{total_combos:,}")
    
    if total_combos > 1000:
        st.warning("⚠️ Nombre élevé de combinaisons")
    
    return param_grid
