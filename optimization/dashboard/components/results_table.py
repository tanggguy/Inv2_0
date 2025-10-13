#!/usr/bin/env python3
"""
Composants de tableaux pour le dashboard
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from optimization.results_storage import ResultsStorage


def display_runs_table(
    runs: List[Dict], selectable: bool = False, show_actions: bool = True
) -> List[str]:
    """
    Affiche un tableau de runs avec filtres

    Args:
        runs: Liste de runs
        selectable: Permettre la sélection multiple
        show_actions: Afficher les boutons d'action

    Returns:
        Liste des run_ids sélectionnés (si selectable=True)
    """
    if not runs:
        st.info("Aucun run disponible")
        return []

    # Convertir en DataFrame
    df = pd.DataFrame(runs)

    # Colonnes à afficher
    display_cols = [
        "run_id",
        "strategy",
        "type",
        "best_sharpe",
        "best_return",
        "total_combos",
        "symbols",
        "timestamp",
    ]

    # Vérifier les colonnes disponibles
    available_cols = [col for col in display_cols if col in df.columns]
    df_display = df[available_cols].copy()

    # Formater
    if "best_sharpe" in df_display.columns:
        df_display["best_sharpe"] = df_display["best_sharpe"].round(2)
    if "best_return" in df_display.columns:
        df_display["best_return"] = df_display["best_return"].round(2)
    if "timestamp" in df_display.columns:
        df_display["timestamp"] = pd.to_datetime(df_display["timestamp"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
    if "symbols" in df_display.columns:
        df_display["symbols"] = df_display["symbols"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )

    # Renommer colonnes
    rename_map = {
        "run_id": "Run ID",
        "strategy": "Stratégie",
        "type": "Type",
        "best_sharpe": "Sharpe",
        "best_return": "Return (%)",
        "total_combos": "Combos",
        "symbols": "Symboles",
        "timestamp": "Date",
    }
    df_display = df_display.rename(columns=rename_map)

    # Mode sélection
    selected_runs = []

    if selectable:
        # Ajouter une colonne de sélection
        selection = st.data_editor(
            df_display,
            hide_index=True,
            use_container_width=True,
            disabled=[col for col in df_display.columns],
            column_config={
                "_selected": st.column_config.CheckboxColumn(
                    "Sélectionner",
                    help="Sélectionner pour comparaison",
                    default=False,
                )
            },
        )

        # Note: Cette approche simplifiée, pour une vraie sélection multi,
        # il faudrait utiliser st.multiselect ou un custom component

    else:
        # Simple affichage
        st.dataframe(df_display, hide_index=True, use_container_width=True, height=400)

    # Actions
    if show_actions and not df_display.empty:
        st.markdown("### ⚙️ Actions")

        cols = st.columns([1, 1, 1, 2])

        with cols[0]:
            selected_run = st.selectbox(
                "Sélectionner un run",
                options=df["run_id"].tolist(),
                format_func=lambda x: x[:30] + "..." if len(x) > 30 else x,
                key="action_run_select",
            )

        with cols[1]:
            if st.button("🔬 Analyser", use_container_width=True):
                st.session_state["active_run"] = selected_run
                st.switch_page("pages/4_🔬_Analyze_Strategy.py")

        with cols[2]:
            if st.button("🗑️ Supprimer", use_container_width=True):
                storage = ResultsStorage()
                if storage.delete_run(selected_run):
                    st.success(f"✅ Run supprimé: {selected_run[:20]}...")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la suppression")

    return selected_runs


def display_comparison_table(runs_data: Dict[str, Dict]):
    """
    Affiche un tableau comparatif de runs

    Args:
        runs_data: Dict {run_id: run_summary}
    """
    if not runs_data:
        st.warning("Aucun run à comparer")
        return

    # Créer le DataFrame comparatif
    comparison_data = []

    for run_id, data in runs_data.items():
        summary = data.get("summary", {})
        best = summary.get("best_params", {})

        row = {
            "Run ID": run_id[:30] + "..." if len(run_id) > 30 else run_id,
            "Stratégie": summary.get("strategy", "N/A"),
            "Sharpe": best.get("sharpe", 0),
            "Return (%)": best.get("return", 0),
            "Drawdown (%)": abs(best.get("drawdown", 0)),
            "Trades": best.get("trades", 0),
            "Win Rate (%)": best.get("win_rate", 0),
            "Symboles": ", ".join(summary.get("symbols", [])),
        }

        # Ajouter les paramètres
        for key, value in best.items():
            if key not in ["sharpe", "return", "drawdown", "trades", "win_rate"]:
                row[key] = value

        comparison_data.append(row)

    df = pd.DataFrame(comparison_data)

    # Formater
    for col in ["Sharpe", "Return (%)", "Drawdown (%)", "Win Rate (%)"]:
        if col in df.columns:
            df[col] = df[col].round(2)

    # Afficher avec mise en forme conditionnelle
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Sharpe": st.column_config.NumberColumn(
                "Sharpe", help="Sharpe Ratio", format="%.2f"
            ),
            "Return (%)": st.column_config.NumberColumn(
                "Return (%)", help="Rendement total", format="%.2f"
            ),
        },
    )


def display_parameters_comparison(runs_data: Dict[str, Dict]):
    """
    Affiche une comparaison des paramètres

    Args:
        runs_data: Dict {run_id: run_summary}
    """
    if not runs_data:
        return

    st.markdown("### 🎯 Comparaison des Paramètres")

    # Extraire tous les paramètres uniques
    all_params = set()
    exclude_keys = [
        "sharpe",
        "return",
        "drawdown",
        "trades",
        "win_rate",
        "avg_win",
        "avg_loss",
    ]

    for run_id, data in runs_data.items():
        best = data.get("summary", {}).get("best_params", {})
        params = {k: v for k, v in best.items() if k not in exclude_keys}
        all_params.update(params.keys())

    if not all_params:
        st.info("Aucun paramètre à comparer")
        return

    # Créer le tableau
    param_data = []

    for param in sorted(all_params):
        row = {"Paramètre": param.replace("_", " ").title()}

        for run_id, data in runs_data.items():
            best = data.get("summary", {}).get("best_params", {})
            value = best.get(param, "-")
            row[run_id[:20]] = value

        param_data.append(row)

    df = pd.DataFrame(param_data)

    st.dataframe(df, hide_index=True, use_container_width=True)


def display_detailed_results_table(results_df: pd.DataFrame, max_rows: int = 100):
    """
    Affiche le tableau détaillé de tous les résultats

    Args:
        results_df: DataFrame avec tous les résultats
        max_rows: Nombre max de lignes à afficher
    """
    if results_df is None or results_df.empty:
        st.warning("Aucun résultat détaillé disponible")
        return

    st.markdown(f"### 📊 Résultats Détaillés ({len(results_df)} combinaisons)")

    # Tri
    sort_by = st.selectbox(
        "Trier par",
        options=["sharpe", "return", "drawdown", "trades", "win_rate"],
        format_func=lambda x: x.capitalize(),
    )

    sort_order = st.radio(
        "Ordre", options=["Décroissant", "Croissant"], horizontal=True
    )

    # Trier
    ascending = sort_order == "Croissant"
    sorted_df = results_df.sort_values(sort_by, ascending=ascending)

    # Limiter
    display_df = sorted_df.head(max_rows).copy()

    # Formater
    for col in ["sharpe", "return", "drawdown", "win_rate"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)

    # Afficher
    st.dataframe(display_df, hide_index=True, use_container_width=True, height=400)

    # Stats
    with st.expander("📈 Statistiques"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Meilleur Sharpe", f"{results_df['sharpe'].max():.2f}")
            st.metric("Sharpe Moyen", f"{results_df['sharpe'].mean():.2f}")

        with col2:
            st.metric("Meilleur Return", f"{results_df['return'].max():.2f}%")
            st.metric("Return Moyen", f"{results_df['return'].mean():.2f}%")

        with col3:
            st.metric("Pire Drawdown", f"{results_df['drawdown'].min():.2f}%")
            st.metric("Drawdown Moyen", f"{results_df['drawdown'].mean():.2f}%")


def create_filterable_table(runs: List[Dict]) -> pd.DataFrame:
    """
    Crée un tableau filtrable de runs

    Args:
        runs: Liste de runs

    Returns:
        DataFrame filtré
    """
    if not runs:
        return pd.DataFrame()

    df = pd.DataFrame(runs)

    st.markdown("### 🔍 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Filtre par stratégie
        strategies = ["Toutes"] + sorted(df["strategy"].unique().tolist())
        selected_strategy = st.selectbox("Stratégie", strategies)

        if selected_strategy != "Toutes":
            df = df[df["strategy"] == selected_strategy]

    with col2:
        # Filtre par type
        types = ["Tous"] + sorted(df["type"].unique().tolist())
        selected_type = st.selectbox("Type d'optimisation", types)

        if selected_type != "Tous":
            df = df[df["type"] == selected_type]

    with col3:
        # Filtre par Sharpe minimum
        min_sharpe = st.number_input(
            "Sharpe minimum", min_value=0.0, max_value=10.0, value=0.0, step=0.1
        )

        df = df[df["best_sharpe"] >= min_sharpe]

    st.info(f"📊 {len(df)} runs correspondent aux filtres")

    return df
