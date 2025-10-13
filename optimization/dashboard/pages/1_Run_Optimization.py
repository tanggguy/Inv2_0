#!/usr/bin/env python3
"""
Page 1: Lancer une Optimisation
VERSION CORRIGÉE - Compatible Optuna + Streamlit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import time
from optimization.optimizer import UnifiedOptimizer
from optimization.results_storage import ResultsStorage
from dashboard.components.optimizer_form import create_optimization_form
from dashboard.components.metrics import (
    display_metric_cards,
    display_detailed_metrics,
    display_parameters_card,
)
from dashboard.utils.session_state import init_session_state

# Configuration
st.set_page_config(page_title="Run Optimization", page_icon="🚀", layout="wide")

# Initialiser le state
init_session_state()

# Header
st.title("🚀 Lancer une Optimisation")
st.markdown("Configurez et lancez une optimisation de stratégie")

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
        disabled=st.session_state.get("optimization_running", False),
    )

with col2:
    if st.session_state.get("optimization_running", False):
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

    # Avertissement pour Optuna
    if opt_type == "optuna":
        st.info(
            "ℹ️ Optuna: Mode séquentiel activé pour compatibilité avec Streamlit. "
            "Pour parallélisation complète, utilisez le script CLI."
        )

    progress_bar = st.progress(0)
    status_text = st.empty()
    eta_text = st.empty()

    try:
        # CORRECTION: Désactiver parallélisation pour Optuna avec Streamlit
        use_parallel = False if opt_type == "optuna" else True

        # Créer l'optimiseur
        optimizer = UnifiedOptimizer(
            strategy_class=strategy_class,
            config=config,
            optimization_type=opt_type,
            verbose=False,
            use_parallel=use_parallel,  # ✅ Conditionnel
        )

        st.session_state.current_run_id = optimizer.run_id

        # État partagé pour progression (thread-safe)
        import threading

        progress_lock = threading.Lock()
        progress_state = {"progress": 0.0, "eta": 0, "last_update": time.time()}

        # Callback thread-safe avec throttling
        def progress_callback(progress, eta_seconds):
            """Callback qui met à jour l'état sans toucher directement Streamlit"""
            with progress_lock:
                current_time = time.time()

                # Throttle: max 2 updates/seconde
                if current_time - progress_state["last_update"] < 0.5:
                    return

                progress_state["progress"] = min(progress, 1.0)
                progress_state["eta"] = max(eta_seconds, 0)
                progress_state["last_update"] = current_time

        # Container pour résultats
        results_container = {"results": None, "error": None, "done": False}

        # Fonction d'optimisation dans thread
        def run_optimization():
            try:
                results_container["results"] = optimizer.run(
                    progress_callback=progress_callback
                )
            except Exception as e:
                results_container["error"] = e
            finally:
                results_container["done"] = True

        # Lancer dans un thread
        opt_thread = threading.Thread(target=run_optimization, daemon=True)
        opt_thread.start()

        # Boucle de mise à jour de l'UI (thread principal)
        max_wait = 7200  # 2 heures max
        start_time = time.time()

        while not results_container["done"] and (time.time() - start_time) < max_wait:
            # Lire l'état de progression
            with progress_lock:
                current_progress = progress_state["progress"]
                current_eta = progress_state["eta"]

            # Mettre à jour l'UI (safe, on est dans le thread principal)
            progress_bar.progress(current_progress)

            # Formater et afficher le statut
            if current_eta > 0:
                eta_minutes = current_eta // 60
                eta_seconds = current_eta % 60
                status_text.text(
                    f"⏳ Progression: {current_progress*100:.1f}% - "
                    f"Reste: {int(eta_minutes)}m {int(eta_seconds)}s"
                )
            else:
                status_text.text(f"⏳ Progression: {current_progress*100:.1f}%")

            # Petit sleep pour ne pas spammer
            time.sleep(0.5)

        # Attendre la fin du thread
        opt_thread.join(timeout=5)

        # Vérifier les erreurs
        if results_container["error"]:
            raise results_container["error"]

        results = results_container["results"]

        # Succès
        if results and "best" in results:
            progress_bar.progress(1.0)
            status_text.empty()
            eta_text.empty()

            st.success("✅ Optimisation terminée avec succès !")

            # Métriques principales
            st.divider()
            st.markdown("### 🏆 Meilleurs Résultats")
            display_metric_cards(results["best"])

            # Paramètres optimaux
            st.divider()
            st.markdown("### 🎯 Paramètres Optimaux")
            display_parameters_card(results["best"])

            # Métriques détaillées
            st.divider()
            st.markdown("### 📊 Analyse Détaillée")
            display_detailed_metrics(results["best"])

            # Évaluation Sharpe
            sharpe = results["best"].get("sharpe", 0)
            st.divider()
            st.markdown("### 📈 Évaluation de la Performance")

            if sharpe > 2.5:
                st.success(
                    "⭐⭐⭐⭐⭐ EXCELLENTE performance ! Stratégie très prometteuse."
                )
            elif sharpe > 2.0:
                st.success("⭐⭐⭐⭐ TRÈS BONNE performance. Stratégie solide.")
            elif sharpe > 1.5:
                st.info("⭐⭐⭐ BONNE performance. Stratégie acceptable.")
            elif sharpe > 1:
                st.warning("⭐⭐ Performance MOYENNE. À améliorer.")
            else:
                st.error("⭐ Performance FAIBLE. Revoir la stratégie.")

            # Importance des paramètres (Optuna uniquement)
            if opt_type == "optuna" and "param_importance" in results:
                st.divider()
                st.markdown("### 🔍 Importance des Paramètres")

                import pandas as pd

                importance = results["param_importance"]
                if importance:
                    df = pd.DataFrame(
                        [
                            {"Paramètre": k, "Importance": v}
                            for k, v in sorted(
                                importance.items(), key=lambda x: x[1], reverse=True
                            )
                        ]
                    )

                    st.dataframe(df, use_container_width=True)

                    st.info(
                        "💡 Les paramètres avec une importance élevée ont le plus d'impact sur la performance."
                    )

            # Sauvegarder dans session state
            st.session_state.last_optimization_results = results
            st.session_state.optimization_running = False

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
    st.markdown(
        """
    ### 🎯 Workflow d'Optimisation
    
    1. **Choisir une stratégie** : Sélectionnez la stratégie à optimiser
    2. **Configurer les paramètres** : Utilisez un preset ou personnalisez
    3. **Lancer l'optimisation** : Le système teste différentes combinaisons
    4. **Analyser les résultats** : Consultez les métriques et paramètres optimaux
    
    ### 🔬 Types d'Optimisation
    
    - **Grid Search** : Test exhaustif (parallélisé)
    - **Walk-Forward** : Validation robuste
    - **Optuna** : Optimisation Bayésienne (50-100x plus rapide)
    
    ### ⚠️ Note pour Optuna + Streamlit
    
    Optuna est exécuté en mode séquentiel dans le dashboard pour compatibilité.
    Pour la parallélisation complète, utilisez:
    ```bash
    python quick_optimize.py
    ```
    """
    )

# Footer
st.divider()
st.caption(
    "💡 Astuce: Pour des optimisations longues avec parallélisation, utilisez le script CLI."
)
