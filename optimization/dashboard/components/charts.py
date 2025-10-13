#!/usr/bin/env python3
"""
Graphiques Plotly pour le dashboard
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional


def create_equity_curve(results_df: pd.DataFrame, run_id: str = None) -> go.Figure:
    """
    Crée une equity curve

    Args:
        results_df: DataFrame avec colonnes ['date', 'equity'] ou liste de trades
        run_id: ID du run pour le titre

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    # Si c'est une série de trades, calculer l'equity curve
    if "pnl" in results_df.columns:
        equity = results_df["pnl"].cumsum() + 100000  # Supposer capital initial 100k
        fig.add_trace(
            go.Scatter(
                y=equity,
                mode="lines",
                name="Equity",
                line=dict(color="#667eea", width=2),
                fill="tozeroy",
                fillcolor="rgba(102, 126, 234, 0.1)",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=results_df.index if results_df.index.name else range(len(results_df)),
                y=(
                    results_df["equity"]
                    if "equity" in results_df
                    else results_df.iloc[:, 0]
                ),
                mode="lines",
                name="Equity",
                line=dict(color="#667eea", width=2),
                fill="tozeroy",
                fillcolor="rgba(102, 126, 234, 0.1)",
            )
        )

    fig.update_layout(
        title=f'Equity Curve {f"- {run_id}" if run_id else ""}',
        xaxis_title="Date/Trade",
        yaxis_title="Capital ($)",
        template="plotly_dark",
        hovermode="x unified",
        height=400,
    )

    return fig


def create_drawdown_chart(results_df: pd.DataFrame, run_id: str = None) -> go.Figure:
    """
    Crée un graphique de drawdown

    Args:
        results_df: DataFrame avec equity
        run_id: ID du run

    Returns:
        Figure Plotly
    """
    # Calculer le drawdown
    if "equity" in results_df.columns:
        equity = results_df["equity"]
    else:
        equity = results_df.iloc[:, 0]

    running_max = equity.expanding().max()
    drawdown = (equity - running_max) / running_max * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=drawdown.index if hasattr(drawdown, "index") else range(len(drawdown)),
            y=drawdown,
            mode="lines",
            name="Drawdown",
            line=dict(color="#f87171", width=2),
            fill="tozeroy",
            fillcolor="rgba(248, 113, 113, 0.2)",
        )
    )

    fig.update_layout(
        title=f'Drawdown {f"- {run_id}" if run_id else ""}',
        xaxis_title="Date/Trade",
        yaxis_title="Drawdown (%)",
        template="plotly_dark",
        hovermode="x unified",
        height=300,
    )

    return fig


def create_comparison_chart(runs_data: Dict[str, pd.DataFrame]) -> go.Figure:
    """
    Compare plusieurs equity curves

    Args:
        runs_data: Dict {run_id: results_df}

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    colors = ["#667eea", "#f87171", "#34d399", "#fbbf24", "#a78bfa"]

    for i, (run_id, df) in enumerate(runs_data.items()):
        if "equity" in df.columns:
            equity = df["equity"]
        elif "pnl" in df.columns:
            equity = df["pnl"].cumsum() + 100000
        else:
            equity = df.iloc[:, 0]

        fig.add_trace(
            go.Scatter(
                y=equity,
                mode="lines",
                name=run_id[:20],  # Limiter la longueur
                line=dict(color=colors[i % len(colors)], width=2),
            )
        )

    fig.update_layout(
        title="Comparaison des Equity Curves",
        xaxis_title="Trade/Période",
        yaxis_title="Capital ($)",
        template="plotly_dark",
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_heatmap(
    results_df: pd.DataFrame, x_param: str, y_param: str, metric: str = "sharpe"
) -> go.Figure:
    """
    Crée une heatmap paramètres vs métrique

    Args:
        results_df: DataFrame avec résultats
        x_param: Paramètre pour axe X
        y_param: Paramètre pour axe Y
        metric: Métrique à afficher

    Returns:
        Figure Plotly
    """
    # Créer un pivot table
    pivot = results_df.pivot_table(
        values=metric, index=y_param, columns=x_param, aggfunc="mean"
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="RdYlGn",
            text=pivot.values,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            colorbar=dict(title=metric.capitalize()),
        )
    )

    fig.update_layout(
        title=f"Heatmap: {x_param} vs {y_param} ({metric})",
        xaxis_title=x_param,
        yaxis_title=y_param,
        template="plotly_dark",
        height=500,
    )

    return fig


def create_walk_forward_analysis(wf_results: List[Dict]) -> go.Figure:
    """
    Crée un graphique d'analyse Walk-Forward

    Args:
        wf_results: Liste des résultats walk-forward

    Returns:
        Figure Plotly avec In-Sample vs Out-Sample
    """
    df = pd.DataFrame(wf_results)

    fig = go.Figure()

    # In-Sample
    fig.add_trace(
        go.Bar(
            x=df["period"],
            y=df["in_sharpe"],
            name="In-Sample",
            marker_color="#667eea",
            text=df["in_sharpe"].round(2),
            textposition="outside",
        )
    )

    # Out-Sample
    fig.add_trace(
        go.Bar(
            x=df["period"],
            y=df["out_sharpe"],
            name="Out-Sample",
            marker_color="#f87171",
            text=df["out_sharpe"].round(2),
            textposition="outside",
        )
    )

    fig.update_layout(
        title="Walk-Forward Analysis: In-Sample vs Out-Sample",
        xaxis_title="Période",
        yaxis_title="Sharpe Ratio",
        template="plotly_dark",
        barmode="group",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_distribution_chart(
    results_df: pd.DataFrame, metric: str = "sharpe"
) -> go.Figure:
    """
    Crée un histogramme de distribution

    Args:
        results_df: DataFrame avec résultats
        metric: Métrique à afficher

    Returns:
        Figure Plotly
    """
    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=results_df[metric],
            nbinsx=30,
            name=metric.capitalize(),
            marker_color="#667eea",
            opacity=0.7,
        )
    )

    # Ajouter une ligne verticale pour la médiane
    median_value = results_df[metric].median()
    fig.add_vline(
        x=median_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Médiane: {median_value:.2f}",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"Distribution de {metric.capitalize()}",
        xaxis_title=metric.capitalize(),
        yaxis_title="Fréquence",
        template="plotly_dark",
        height=400,
    )

    return fig


def create_scatter_plot(
    results_df: pd.DataFrame,
    x_metric: str = "return",
    y_metric: str = "sharpe",
    color_by: Optional[str] = None,
) -> go.Figure:
    """
    Crée un scatter plot

    Args:
        results_df: DataFrame avec résultats
        x_metric: Métrique pour axe X
        y_metric: Métrique pour axe Y
        color_by: Paramètre pour colorer les points

    Returns:
        Figure Plotly
    """
    if color_by and color_by in results_df.columns:
        fig = px.scatter(
            results_df,
            x=x_metric,
            y=y_metric,
            color=color_by,
            template="plotly_dark",
            height=500,
            hover_data=results_df.columns,
        )
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=results_df[x_metric],
                y=results_df[y_metric],
                mode="markers",
                marker=dict(
                    size=8,
                    color=results_df[y_metric],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title=y_metric.capitalize()),
                ),
                text=results_df.index,
                hovertemplate="<b>%{text}</b><br>"
                + f"{x_metric}: %{{x:.2f}}<br>"
                + f"{y_metric}: %{{y:.2f}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"{y_metric.capitalize()} vs {x_metric.capitalize()}",
        xaxis_title=x_metric.capitalize(),
        yaxis_title=y_metric.capitalize(),
        template="plotly_dark",
        height=500,
    )

    return fig


def create_parameter_impact_chart(
    results_df: pd.DataFrame, param: str, metric: str = "sharpe"
) -> go.Figure:
    """
    Montre l'impact d'un paramètre sur une métrique

    Args:
        results_df: DataFrame avec résultats
        param: Paramètre à analyser
        metric: Métrique cible

    Returns:
        Figure Plotly
    """
    # Grouper par paramètre et calculer la moyenne
    grouped = (
        results_df.groupby(param)[metric].agg(["mean", "std", "count"]).reset_index()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=grouped[param],
            y=grouped["mean"],
            mode="lines+markers",
            name="Moyenne",
            line=dict(color="#667eea", width=3),
            marker=dict(size=10),
            error_y=dict(
                type="data",
                array=grouped["std"],
                visible=True,
                color="rgba(102, 126, 234, 0.3)",
            ),
        )
    )

    fig.update_layout(
        title=f"Impact de {param} sur {metric.capitalize()}",
        xaxis_title=param,
        yaxis_title=f"{metric.capitalize()} (moyenne ± std)",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )

    return fig
