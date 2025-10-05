#!/usr/bin/env python3
"""
Page 1: Lancer une Optimisation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import time
from optimization.optimizer import UnifiedOptimizer

from optimization.results_storage import ResultsStorage
from dashboard.components.optimizer_form import create_optimization_form
from dashboard.components.metrics import display_metric_cards, display_detailed_metrics, display_parameters_card, display_copy_button
from dashboard.utils.session_state import init_session_state

# Configuration
st.set_page_config(
    page_title="Run Optimization",
    page_icon="🚀",
    layout="wide"
)

# Initialiser le state
init_session_state()

# Header
st.title("🚀 Lancer une Optimisation")
st.markdown("Configurez et lancez une optimisation de stratégie avec Grid Search ou Walk-Forward")

st.divider()

# Formulaire de configuration
strategy_class, config, opt_type = create_optimization_form()

st.divider()

# Bouton de lancement
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    run_button = st.button(
        "▶️ Lancer l'Optimisation",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.get('optimization_running', False)
    )

with col2:
    if st.session_state.get('optimization_running', False):
        if st.button("⏹️ Annuler", use_container_width=True):
            st.session_state.optimization_running = False
            st.warning("⚠️ Optimisation annulée")
            st.rerun()

# Lancer l'optimisation
if run_button and strategy_class and config and opt_type:
    
    st.session_state.optimization_running = True
    
    # Zone de progression
    st.markdown("---")
    st.markdown("### 📊 Optimisation en cours...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Créer l'optimiseur
        optimizer = UnifiedOptimizer(
            strategy_class=strategy_class,
            config=config,
            optimization_type=opt_type,
            verbose=False  # Pas de logs dans la console
        )
        
        st.session_state.current_run_id = optimizer.run_id
        
        # Callback de progression
        def progress_callback(progress):
            progress_bar.progress(progress)
            status_text.text(f"Progression: {progress*100:.1f}% - Run ID: {optimizer.run_id}")
        
        # Lancer l'optimisation
        with st.spinner('Optimisation en cours...'):
            results = optimizer.run(progress_callback=progress_callback)
        
        # Succès
        if results and 'best' in results:
            st.success("✅ Optimisation terminée avec succès !")
            
            st.markdown("---")
            st.markdown("## 🏆 Résultats")
            
            # Métriques principales
            display_metric_cards(results)
            
            # Métriques détaillées
            display_detailed_metrics(results)
            
            st.divider()
            
            # Paramètres
            col1, col2 = st.columns([2, 1])
            
            with col1:
                display_parameters_card(results['best'])
            
            with col2:
                st.markdown("### 📋 Actions")
                
                if st.button("🔬 Analyser en détail", use_container_width=True):
                    st.session_state.active_run = results['run_id']
                    st.switch_page("pages/4_🔬_Analyze_Strategy.py")
                
                if st.button("📋 Voir l'historique", use_container_width=True):
                    st.switch_page("pages/2_📋_View_History.py")
            
            st.divider()
            
            # Copier les paramètres
            st.markdown("### 📋 Copier les Meilleurs Paramètres")
            display_copy_button(results['best'])
            
            # Sauvegarder dans le state
            st.session_state.last_optimization_results = results
            
        else:
            st.error("❌ L'optimisation n'a produit aucun résultat")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'optimisation: {e}")
        import traceback
        with st.expander("🔍 Détails de l'erreur"):
            st.code(traceback.format_exc())
    
    finally:
        st.session_state.optimization_running = False
        progress_bar.progress(100)

# Afficher les derniers résultats si disponibles
elif st.session_state.get('last_optimization_results'):
    st.markdown("---")
    st.markdown("## 📊 Dernière Optimisation")
    
    results = st.session_state.last_optimization_results
    
    with st.expander("🔍 Voir les résultats", expanded=False):
        display_metric_cards(results)
        display_detailed_metrics(results)
        display_parameters_card(results['best'])

# Instructions
if not st.session_state.get('optimization_running', False):
    st.markdown("---")
    st.markdown("""
    ### 💡 Instructions
    
    1. **Sélectionnez une stratégie** à optimiser
    2. **Choisissez un preset** ou personnalisez la configuration
    3. **Sélectionnez le type** d'optimisation (Grid Search ou Walk-Forward)
    4. **Personnalisez** (optionnel) les symboles, période, capital
    5. **Lancez** l'optimisation et suivez la progression
    
    ⏱️ La durée dépend du nombre de combinaisons à tester. Les résultats seront sauvegardés automatiquement.
    """)