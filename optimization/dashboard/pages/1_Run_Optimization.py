#!/usr/bin/env python3
"""
Page 1: Lancer une Optimisation
AVEC PROGRESSION FLUIDE ET ESTIMATION DU TEMPS RESTANT
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
    eta_text = st.empty()
    
    try:
        # Créer l'optimiseur
        optimizer = UnifiedOptimizer(
            strategy_class=strategy_class,
            config=config,
            optimization_type=opt_type,
            verbose=False  # Pas de logs dans la console
        )
        
        st.session_state.current_run_id = optimizer.run_id
        
        # Callback de progression AMÉLIORÉ avec ETA
        def progress_callback(progress, eta_seconds):
            """
            Callback appelé à chaque itération
            
            Args:
                progress: Pourcentage de progression (0.0 à 1.0)
                eta_seconds: Temps restant estimé en secondes
            """
            # Mettre à jour la barre de progression
            progress_bar.progress(progress)
            
            # Afficher le pourcentage
            status_text.text(f"Progression: {progress*100:.1f}% - Run ID: {optimizer.run_id}")
            
            # Afficher le temps restant
            if eta_seconds > 0:
                # Convertir en minutes et secondes
                minutes = int(eta_seconds // 60)
                seconds = int(eta_seconds % 60)
                
                if minutes > 0:
                    eta_text.info(f"⏱️ Temps restant estimé: {minutes}m {seconds}s")
                else:
                    eta_text.info(f"⏱️ Temps restant estimé: {seconds}s")
            else:
                eta_text.info("⏱️ Calcul du temps restant...")
        
        # Lancer l'optimisation
        with st.spinner('Optimisation en cours...'):
            results = optimizer.run(progress_callback=progress_callback)
        
        # Succès
        if results and 'best' in results:
            st.success("✅ Optimisation terminée avec succès !")
            
            # Stocker les résultats dans la session
            st.session_state.last_optimization_results = results
            st.session_state.optimization_running = False
            
            st.divider()
            
            # Afficher les résultats
            st.markdown("## 🏆 Résultats de l'Optimisation")
            
            # Métriques principales
            display_metric_cards(results)
            
            # Métriques détaillées
            display_detailed_metrics(results)
            
            st.divider()
            
            # Paramètres optimaux
            col1, col2 = st.columns(2)
            
            with col1:
                display_parameters_card(results['best'])
            
            with col2:
                st.markdown("### 📋 Actions")
                
                # Bouton pour copier les paramètres
                display_copy_button(results['best'])
                
                # Lien vers l'analyse détaillée
                if st.button("🔬 Voir l'Analyse Détaillée", use_container_width=True):
                    st.switch_page("pages/4_Analyze_Strategy.py")
                
                # Lien vers l'historique
                if st.button("📋 Voir l'Historique", use_container_width=True):
                    st.switch_page("pages/2_View_History.py")
            
            # Évaluation de la performance
            st.divider()
            st.markdown("### 💡 Évaluation")
            
            sharpe = results['best'].get('sharpe', 0)
            
            if sharpe > 2:
                st.success("⭐⭐⭐⭐⭐ EXCELLENTE performance ! Stratégie très prometteuse.")
            elif sharpe > 1.5:
                st.success("⭐⭐⭐⭐ TRÈS BONNE performance. Stratégie solide.")
            elif sharpe > 1:
                st.info("⭐⭐⭐ BONNE performance. Stratégie acceptable.")
            elif sharpe > 0.5:
                st.warning("⭐⭐ Performance ACCEPTABLE. À améliorer.")
            else:
                st.error("⭐ Performance FAIBLE. Revoir la stratégie.")
            
            # Walk-Forward
            if opt_type == "walk_forward" and 'walk_forward_results' in results:
                st.divider()
                st.markdown("### 📊 Analyse Walk-Forward")
                from dashboard.components.metrics import display_walk_forward_metrics
                display_walk_forward_metrics(results['walk_forward_results'])
        
        else:
            st.error("❌ Échec de l'optimisation - Aucun résultat valide")
            st.session_state.optimization_running = False
    
    except Exception as e:
        st.error(f"❌ Erreur pendant l'optimisation: {str(e)}")
        st.session_state.optimization_running = False
        
        # Afficher le traceback pour debug
        with st.expander("🔍 Détails de l'erreur"):
            import traceback
            st.code(traceback.format_exc())

# Aide
with st.expander("ℹ️ Comment ça marche ?"):
    st.markdown("""
    ### 🎯 Workflow d'Optimisation
    
    1. **Choisir une stratégie** : Sélectionnez la stratégie à optimiser
    2. **Configurer les paramètres** : Utilisez un preset ou personnalisez
    3. **Lancer l'optimisation** : Le système teste toutes les combinaisons
    4. **Analyser les résultats** : Consultez les métriques et paramètres optimaux
    
    ### 📊 Types d'Optimisation
    
    - **Grid Search** : Test exhaustif de toutes les combinaisons (parallélisé)
    - **Walk-Forward** : Validation robuste contre l'overfitting
    
    ### ⏱️ Estimation du temps
    
    Le système affiche en temps réel:
    - La progression en pourcentage
    - Le temps restant estimé en minutes et secondes
    - Le nombre de combinaisons testées
    
    ### 🚀 Performance
    
    La parallélisation permet de tester **4 à 8 fois plus vite** qu'en mode séquentiel.
    """)

# Footer
st.divider()
st.markdown("---")
st.caption("💡 Astuce: Utilisez les presets pour démarrer rapidement, puis personnalisez selon vos besoins.")