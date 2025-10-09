#!/usr/bin/env python3
"""
Formulaire pour lancer une optimisation
"""

import streamlit as st
from typing import Dict, Tuple, Optional
from optimization.optimization_config import OptimizationConfig
import importlib
from datetime import datetime
from components.optuna_components import display_optuna_config_section


def get_available_strategies() -> Dict[str, type]:
    """Récupère les stratégies disponibles"""
    strategies = {}
    
    # Import des stratégies de base
    try:
        from strategies.masuperstrategie import MaSuperStrategie
        strategies['MaSuperStrategie'] = MaSuperStrategie
    except:
        pass
    
    try:
        from strategies.moving_average import MovingAverageStrategy
        strategies['MovingAverage'] = MovingAverageStrategy
    except:
        pass
    
    try:
        from strategies.rsi_strategy import RSIStrategy
        strategies['RSI'] = RSIStrategy
    except:
        pass
    try:
        from strategies.bollingerbands import MeanReversionStrategy
        strategies['BollingerBands'] = MeanReversionStrategy
    except:
        pass
    try:
        from strategies.squeezemomentumstrategy import SqueezeMomentumStrategy
        strategies['SqueezeMomentum'] = SqueezeMomentumStrategy
    except:
        pass
    # Stratégies avancées
    try:
        from strategies.advanced_strategies import (
            MACrossoverAdvanced,
            RSITrailingStop,
            BreakoutATRStop,
            MomentumMultipleStops
        )
        strategies['MACrossoverAdvanced'] = MACrossoverAdvanced
        strategies['RSITrailingStop'] = RSITrailingStop
        strategies['BreakoutATRStop'] = BreakoutATRStop
        strategies['MomentumMultipleStops'] = MomentumMultipleStops
    except:
        pass
    
    return strategies


def display_strategy_selector() -> Tuple[str, Optional[type]]:
    """
    Affiche le sélecteur de stratégie
    
    Returns:
        (strategy_name, strategy_class)
    """
    strategies = get_available_strategies()
    
    if not strategies:
        st.error("❌ Aucune stratégie disponible")
        return None, None
    
    strategy_name = st.selectbox(
        "🎯 Sélectionner une stratégie",
        options=list(strategies.keys()),
        help="Choisissez la stratégie à optimiser"
    )
    
    # Afficher la description si disponible
    strategy_class = strategies[strategy_name]
    if strategy_class.__doc__:
        with st.expander("ℹ️ Description de la stratégie"):
            st.markdown(strategy_class.__doc__)
    
    return strategy_name, strategy_class


def display_preset_selector(strategy_name: str = None) -> Tuple[str, Dict]:
    """
    Affiche le sélecteur de preset (adapté à la stratégie si fournie)
    
    Args:
        strategy_name: Nom de la stratégie pour adapter le param_grid
    
    Returns:
        (preset_name, config)
    """
    config_manager = OptimizationConfig()
    presets = config_manager.list_presets()
    
    # Sélection du preset
    preset_name = st.selectbox(
        "⚙️ Configuration",
        options=presets,
        format_func=lambda x: x.replace('_', ' ').title(),
        help="Configurations prédéfinies pour l'optimisation"
    )
    
    # 🔥 MODIFICATION CLÉE : Adapter à la stratégie si fournie
    if strategy_name:
        config = config_manager.get_config_for_strategy(
            strategy_name=strategy_name,
            preset_name=preset_name
        )
        
        # Afficher un indicateur si adapté
        if config.get('_metadata', {}).get('adapted'):
            st.success(f"✓ Configuration adaptée pour {strategy_name}")
    else:
        # Fallback : charger le preset brut
        config = config_manager.get_preset(preset_name)
    
    # Afficher le résumé
    with st.expander("📋 Voir le résumé de la configuration"):
        summary = config_manager.get_config_summary(config)
        st.text(summary)
        
        # Afficher les paramètres qui seront optimisés
        st.markdown("#### 🎯 Paramètres à Optimiser")
        param_grid = config.get('param_grid', {})
        
        if param_grid:
            for param, values in param_grid.items():
                st.write(f"  • **{param}**: {values} ({len(values)} valeurs)")
            
            # Calculer combinaisons
            from itertools import product
            total_combos = 1
            for values in param_grid.values():
                total_combos *= len(values)
            
            st.metric("💎 Combinaisons Totales", f"{total_combos:,}")
        else:
            st.warning("⚠️ Aucun paramètre défini pour optimisation")
    
    return preset_name, config

def display_optimization_type_selector() -> str:
    opt_type = st.radio(
        "🔬 Type d'optimisation",
        options=['grid_search', 'walk_forward', 'optuna'],
        format_func=lambda x: {
            'grid_search': '📊 Grid Search',
            'walk_forward': '🚶 Walk-Forward',
            'optuna': '🔬 Optuna - Bayésien (recommandé)'
        }[x]
    )
    
    if opt_type == 'optuna':
        optuna_config = display_optuna_config_section()
        st.session_state.optuna_config = optuna_config
    
    return opt_type


def display_config_customization(config: Dict) -> Dict:
    """
    Affiche les options de personnalisation
    
    Args:
        config: Configuration de base
    
    Returns:
        Configuration personnalisée
    """
    custom_config = config.copy()
    
    with st.expander("🔧 Personnaliser la configuration"):
        
        # Symboles
        st.markdown("#### 📈 Symboles")
        
        current_symbols = ', '.join(config['symbols'])
        new_symbols = st.text_input(
            "Symboles (séparés par des virgules)",
            value=current_symbols,
            help="Ex: AAPL, MSFT, GOOGL"
        )
        
        if new_symbols:
            custom_config['symbols'] = [s.strip() for s in new_symbols.split(',')]
        
        # Période
        st.markdown("#### 📅 Période")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Date de début",
                value=datetime.strptime(config['period']['start'], '%Y-%m-%d'),
                help="Date de début du backtest"
            )
        
        with col2:
            end_date = st.date_input(
                "Date de fin",
                value=datetime.strptime(config['period']['end'], '%Y-%m-%d'),
                help="Date de fin du backtest"
            )
        
        custom_config['period'] = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
        
        # Capital
        st.markdown("#### 💰 Capital Initial")
        
        capital = st.number_input(
            "Capital initial ($)",
            min_value=1000,
            max_value=10000000,
            value=config.get('capital', 100000),
            step=10000,
            help="Capital de départ pour le backtest"
        )
        
        custom_config['capital'] = capital
        
        # Grille de paramètres (affichage uniquement)
        st.markdown("#### 🎛️ Grille de Paramètres")
        
        param_grid = config.get('param_grid', {})
        
        if param_grid:
            for param, values in param_grid.items():
                st.text(f"{param}: {values}")
        
        st.info("💡 Pour modifier la grille de paramètres, éditez le fichier de preset JSON")
    
    return custom_config


def display_optimization_summary(strategy_name: str, config: Dict, opt_type: str):
    """
    Affiche un résumé de l'optimisation avant lancement
    
    Args:
        strategy_name: Nom de la stratégie
        config: Configuration
        opt_type: Type d'optimisation
    """
    st.markdown("### 📋 Résumé de l'Optimisation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**🎯 Stratégie:** {strategy_name}")
        st.markdown(f"**🔬 Type:** {opt_type.replace('_', ' ').title()}")
        st.markdown(f"**📈 Symboles:** {', '.join(config['symbols'])}")
    
    with col2:
        st.markdown(f"**📅 Période:** {config['period']['start']} → {config['period']['end']}")
        st.markdown(f"**💰 Capital:** ${config.get('capital', 100000):,}")
        
        # Calculer le nombre de combinaisons
        from itertools import product
        total_combos = 1
        for values in config['param_grid'].values():
            total_combos *= len(values)
        
        st.markdown(f"**🎲 Combinaisons:** {total_combos:,}")
    
    # Estimation du temps
    avg_time_per_combo = 0.5  # secondes (estimation)
    estimated_time = total_combos * avg_time_per_combo
    
    if estimated_time < 60:
        time_str = f"{estimated_time:.0f} secondes"
    elif estimated_time < 3600:
        time_str = f"{estimated_time/60:.1f} minutes"
    else:
        time_str = f"{estimated_time/3600:.1f} heures"
    
    st.info(f"⏱️ Temps estimé: {time_str}")


def create_optimization_form() -> Tuple[Optional[type], Optional[Dict], Optional[str]]:
    """
    Crée le formulaire complet d'optimisation
    
    Returns:
        (strategy_class, config, opt_type) ou (None, None, None) si incomplet
    """
    st.markdown("## 🚀 Configuration de l'Optimisation")
    
    # Étape 1: Stratégie
    strategy_name, strategy_class = display_strategy_selector()
    
    if not strategy_class:
        return None, None, None
    
    st.divider()
    
    # Étape 2: Preset (avec adaptation automatique)
    # 🔥 MODIFICATION : Passer strategy_name
    preset_name, config = display_preset_selector(strategy_name=strategy_name)
    
    st.divider()
    
    # Étape 3: Type d'optimisation
    opt_type = display_optimization_type_selector()
    
    st.divider()
    
    # Étape 4: Personnalisation (optionnel)
    config = display_config_customization(config)
    
    # 🔥 NOUVELLE VALIDATION : Vérifier cohérence param_grid
    config_manager = OptimizationConfig()
    is_valid, warnings = config_manager.validate_strategy_params(strategy_class, config.get('param_grid', {}))
    
    if warnings:
        with st.expander("⚠️ Avertissements de Validation", expanded=False):
            for warning in warnings:
                st.warning(warning)
    
    st.divider()
    
    # Étape 5: Résumé
    display_optimization_summary(strategy_name, config, opt_type)
    
    return strategy_class, config, opt_type