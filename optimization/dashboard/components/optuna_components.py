#!/usr/bin/env python3
"""
Composants Streamlit pour l'optimisation Optuna

À intégrer dans dashboard/components/optimizer_form.py
"""

import streamlit as st
from typing import Dict, Optional


def display_optuna_config_section() -> Dict:
    """
    Affiche la section de configuration Optuna dans le formulaire
    
    Returns:
        Configuration Optuna
    """
    st.markdown("### 🔬 Configuration Optuna")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_trials = st.number_input(
            "🎯 Nombre de trials",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Plus de trials = meilleure exploration mais plus long"
        )
        
        sampler = st.selectbox(
            "🧠 Algorithme de sampling",
            options=['tpe', 'random'],
            format_func=lambda x: {
                'tpe': '🌳 TPE - Tree-structured Parzen Estimator (recommandé)',
                'random': '🎲 Random - Échantillonnage aléatoire'
            }[x],
            help="TPE est intelligent et apprend des essais précédents"
        )
    
    with col2:
        timeout = st.number_input(
            "⏱️ Timeout (secondes)",
            min_value=0,
            max_value=36000,
            value=0,
            step=300,
            help="0 = pas de limite de temps"
        )
        timeout = timeout if timeout > 0 else None
        
        pruner = st.selectbox(
            "✂️ Stratégie de pruning",
            options=['median', 'successive_halving', 'none'],
            format_func=lambda x: {
                'median': '📊 Median - Arrête les trials sous-performants',
                'successive_halving': '🔪 Successive Halving - Très agressif',
                'none': '🚫 Aucun - Tous les trials jusqu\'au bout'
            }[x],
            help="Le pruning accélère l'optimisation en arrêtant les mauvais essais"
        )
    
    save_plots = st.checkbox(
        "📈 Sauvegarder les visualisations",
        value=True,
        help="Génère des graphiques interactifs (historique, importance, etc.)"
    )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        optimize_metric = st.selectbox(
            "🎯 Métrique à optimiser",
            options=['sharpe', 'return', 'win_rate', 'profit_factor'],
            help="Quelle métrique Optuna doit-il maximiser ?"
        )
        
        parallel = st.checkbox(
            "⚡ Parallélisation",
            value=True,
            help="Utilise tous les CPUs disponibles (plus rapide)"
        )
    
    # Estimation du temps
    st.info(f"""
    ⏱️ **Estimation du temps:**
    - Avec {n_trials} trials
    - ~2-5 secondes par trial (moyenne)
    - **Temps estimé: {n_trials * 3 / 60:.1f} minutes**
    """)
    
    return {
        'n_trials': n_trials,
        'timeout': timeout,
        'sampler': sampler,
        'pruner': pruner,
        'save_plots': save_plots,
        'optimize_metric': optimize_metric,
        'use_parallel': parallel
    }


def display_optuna_results(results: Dict):
    """
    Affiche les résultats d'une optimisation Optuna
    
    Args:
        results: Dictionnaire de résultats
    """
    st.markdown("### 🏆 Résultats Optuna")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Meilleur Sharpe",
            f"{results.get('best', {}).get('sharpe', 0):.2f}"
        )
    
    with col2:
        st.metric(
            "Trials complétés",
            results.get('n_trials', 0)
        )
    
    with col3:
        if 'optuna_study' in results:
            st.metric(
                "Study ID",
                results['optuna_study'][:12] + "..."
            )
    
    with col4:
        st.metric(
            "Return",
            f"{results.get('best', {}).get('return', 0):.1f}%"
        )
    
    # Importance des paramètres
    if 'param_importance' in results and results['param_importance']:
        st.markdown("#### 📊 Importance des Paramètres")
        
        importance = results['param_importance']
        
        # Créer un DataFrame pour l'affichage
        import pandas as pd
        df_importance = pd.DataFrame([
            {'Paramètre': param, 'Importance': imp}
            for param, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)
        ])
        
        # Afficher avec barre de progression
        for _, row in df_importance.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(row['Importance'])
                st.caption(row['Paramètre'])
            with col2:
                st.metric("", f"{row['Importance']:.3f}")
    
    # Lien vers les visualisations
    if results.get('optuna_storage'):
        st.markdown("#### 📈 Visualisations")
        st.info("""
        Les graphiques interactifs Optuna ont été sauvegardés dans:
        `optimization/optuna_plots/`
        
        Pour les voir:
        1. Ouvrez les fichiers .html dans votre navigateur
        2. Ou lancez le dashboard Optuna: `optuna-dashboard {storage_url}`
        """.replace('{storage_url}', results.get('optuna_storage', '')))


def display_optuna_comparison(results_list: list):
    """
    Compare plusieurs optimisations Optuna
    
    Args:
        results_list: Liste de résultats d'optimisation
    """
    import pandas as pd
    import plotly.express as px
    
    st.markdown("### 📊 Comparaison des Optimisations")
    
    # Créer un DataFrame comparatif
    comparison_data = []
    for i, results in enumerate(results_list, 1):
        comparison_data.append({
            'Run': f"Run {i}",
            'Sharpe': results.get('best', {}).get('sharpe', 0),
            'Return': results.get('best', {}).get('return', 0),
            'Drawdown': results.get('best', {}).get('drawdown', 0),
            'Trials': results.get('n_trials', 0),
            'Sampler': results.get('sampler', 'N/A'),
            'Pruner': results.get('pruner', 'N/A')
        })
    
    df = pd.DataFrame(comparison_data)
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True)
    
    # Graphiques de comparaison
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(df, x='Run', y='Sharpe', title='Sharpe Ratio Comparison')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(df, x='Run', y='Return', title='Return Comparison')
        st.plotly_chart(fig, use_container_width=True)


# MODIFICATION À FAIRE DANS optimizer_form.py
"""
Dans la fonction display_optimization_type_selector(), ajouter:

def display_optimization_type_selector() -> str:
    opt_type = st.radio(
        "🔬 Type d'optimisation",
        options=['grid_search', 'walk_forward', 'optuna'],  # <--- AJOUTER 'optuna'
        format_func=lambda x: {
            'grid_search': '📊 Grid Search - Test toutes les combinaisons',
            'walk_forward': '🚶 Walk-Forward - Validation robuste anti-overfitting',
            'optuna': '🔬 Optuna - Optimisation Bayésienne intelligente (recommandé)'  # <--- AJOUTER
        }[x],
        horizontal=True
    )
    
    if opt_type == 'grid_search':
        st.info("💡 Grid Search teste toutes les combinaisons de paramètres. Idéal pour trouver les meilleurs paramètres.")
    elif opt_type == 'walk_forward':
        st.info("💡 Walk-Forward divise les données en périodes In-Sample/Out-Sample pour éviter l'overfitting.")
    elif opt_type == 'optuna':  # <--- AJOUTER
        st.info("💡 Optuna utilise l'optimisation Bayésienne pour explorer intelligemment l'espace des paramètres. 50-100x plus rapide !")
        
        # Afficher la configuration Optuna
        optuna_config = display_optuna_config_section()
        st.session_state.optuna_config = optuna_config
    
    return opt_type
"""