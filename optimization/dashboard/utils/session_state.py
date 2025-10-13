#!/usr/bin/env python3
"""
Gestion de l'état global du dashboard Streamlit
"""

import streamlit as st
from typing import Any, Dict, List


def init_session_state():
    """Initialise le session state avec les valeurs par défaut"""

    # Optimisation en cours
    if "optimization_running" not in st.session_state:
        st.session_state.optimization_running = False

    if "current_run_id" not in st.session_state:
        st.session_state.current_run_id = None

    if "optimization_progress" not in st.session_state:
        st.session_state.optimization_progress = 0.0

    # Sélections
    if "selected_runs" not in st.session_state:
        st.session_state.selected_runs = []

    if "active_run" not in st.session_state:
        st.session_state.active_run = None

    # Configuration
    if "selected_strategy" not in st.session_state:
        st.session_state.selected_strategy = None

    if "selected_preset" not in st.session_state:
        st.session_state.selected_preset = "standard"

    if "custom_config" not in st.session_state:
        st.session_state.custom_config = {}

    # Résultats temporaires
    if "last_optimization_results" not in st.session_state:
        st.session_state.last_optimization_results = None

    # Filtres
    if "history_filters" not in st.session_state:
        st.session_state.history_filters = {}


def update_optimization_progress(progress: float):
    """Met à jour la progression de l'optimisation"""
    st.session_state.optimization_progress = progress


def set_selected_runs(run_ids: List[str]):
    """Définit les runs sélectionnés pour comparaison"""
    st.session_state.selected_runs = run_ids


def set_active_run(run_id: str):
    """Définit le run actif pour analyse détaillée"""
    st.session_state.active_run = run_id


def clear_optimization_state():
    """Réinitialise l'état d'optimisation"""
    st.session_state.optimization_running = False
    st.session_state.current_run_id = None
    st.session_state.optimization_progress = 0.0


def get_state(key: str, default: Any = None) -> Any:
    """Récupère une valeur du session state"""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any):
    """Définit une valeur dans le session state"""
    st.session_state[key] = value
