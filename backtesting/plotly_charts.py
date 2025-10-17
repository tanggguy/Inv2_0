"""
Plotly Charts Generator - Graphiques interactifs pour backtesting multi-symbole

Ce module génère des graphiques Plotly pour:
- Equity curves comparées
- Heatmap de corrélation
- Scatter Return vs Drawdown
- Contributions P&L
- Rolling correlations
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict
from monitoring.logger import setup_logger

logger = setup_logger("plotly_charts")


class PlotlyChartsGenerator:
    """
    Générateur de graphiques Plotly pour backtesting multi-symbole
    """

    def __init__(self, results: Dict):
        """
        Initialise le générateur de graphiques

        Args:
            results: Dict complet des résultats
                    {aggregated: {...}, by_symbol: {...}, daily_returns: {...}, daily_values: {...}}
        """
        self.results = results
        self.aggregated = results.get("aggregated", {})
        self.by_symbol = results.get("by_symbol", {})
        self.daily_returns = results.get("daily_returns", {})
        self.daily_values = results.get("daily_values", {})

        logger.info("PlotlyChartsGenerator initialisé")

    def generate_equity_curves(self) -> go.Figure:
        """
        Génère les equity curves comparées pour tous les symboles

        Returns:
            Figure Plotly
        """
        if not self.daily_values:
            logger.warning("Pas de daily_values disponibles pour equity curves")
            return None

        fig = go.Figure()

        # Palette de couleurs
        colors = px.colors.qualitative.Set2

        # Ajouter une courbe par symbole
        for idx, (symbol, values) in enumerate(self.daily_values.items()):
            color = colors[idx % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values.values,
                    mode="lines",
                    name=symbol,
                    line=dict(width=2, color=color),
                    hovertemplate=(
                        f"<b>{symbol}</b><br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        "Value: $%{y:,.2f}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Layout
        fig.update_layout(
            title={
                "text": "📈 Equity Curves Comparées",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            template="plotly_white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=500,
        )

        # Format axe Y en dollars
        fig.update_yaxes(tickformat="$,.0f")

        logger.info("✓ Equity curves générées")
        return fig

    def generate_correlation_heatmap(
        self, returns_data: Dict[str, pd.Series]
    ) -> go.Figure:
        """
        Génère une heatmap de corrélation

        Args:
            returns_data: Dict {symbol: Series de returns}

        Returns:
            Figure Plotly
        """
        if not returns_data:
            logger.warning("Pas de returns_data pour heatmap")
            return None

        # Calculer matrice de corrélation
        returns_df = pd.DataFrame(returns_data)
        corr_matrix = returns_df.corr()

        # Créer heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdBu_r",  # Rouge = négatif, Bleu = positif
                zmid=0,
                zmin=-1,
                zmax=1,
                text=corr_matrix.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 14},
                colorbar=dict(
                    title="Corrélation",
                    tickvals=[-1, -0.5, 0, 0.5, 1],
                    ticktext=["-1.0", "-0.5", "0", "0.5", "1.0"],
                ),
                hovertemplate=(
                    "%{y} vs %{x}<br>" "Corrélation: %{z:.3f}<br>" "<extra></extra>"
                ),
            )
        )

        # Layout
        fig.update_layout(
            title={
                "text": "🔗 Matrice de Corrélation des Returns",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="",
            yaxis_title="",
            template="plotly_white",
            height=500,
            width=600,
        )

        logger.info("✓ Heatmap de corrélation générée")
        return fig

    def generate_return_vs_drawdown_scatter(self) -> go.Figure:
        """
        Génère un scatter plot Return vs Max Drawdown

        Returns:
            Figure Plotly
        """
        if not self.by_symbol:
            logger.warning("Pas de by_symbol pour scatter plot")
            return None

        # Préparer données
        symbols = []
        returns = []
        drawdowns = []
        sharpes = []

        for symbol, results in self.by_symbol.items():
            symbols.append(symbol)
            returns.append(results.get("total_return", 0))
            drawdowns.append(abs(results.get("max_drawdown", 0)))
            sharpes.append(results.get("sharpe_ratio", 0))

        # Couleur selon Sharpe ratio
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=drawdowns,
                y=returns,
                mode="markers+text",
                marker=dict(
                    size=15,
                    color=sharpes,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Sharpe Ratio"),
                    line=dict(width=1, color="white"),
                ),
                text=symbols,
                textposition="top center",
                textfont=dict(size=12, color="black"),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Return: %{y:.2f}%<br>"
                    "Max Drawdown: %{x:.2f}%<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Layout
        fig.update_layout(
            title={
                "text": "📊 Return vs Drawdown (Risk/Reward)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="Max Drawdown (%)",
            yaxis_title="Total Return (%)",
            template="plotly_white",
            height=500,
            showlegend=False,
        )

        # Ajouter ligne de référence (idéal = haut-gauche)
        fig.add_shape(
            type="line",
            x0=min(drawdowns),
            y0=max(returns),
            x1=max(drawdowns),
            y1=min(returns),
            line=dict(color="red", width=1, dash="dash"),
            opacity=0.3,
        )

        logger.info("✓ Scatter Return vs Drawdown généré")
        return fig

    def generate_pnl_contributions_bar(self) -> go.Figure:
        """
        Génère un bar chart des contributions P&L

        Returns:
            Figure Plotly
        """
        contributions = self.aggregated.get("pnl_contributions", {})

        if not contributions:
            logger.warning("Pas de contributions P&L")
            return None

        # Préparer données
        symbols = list(contributions.keys())
        absolutes = [contributions[s]["absolute"] for s in symbols]
        percentages = [contributions[s]["percentage"] for s in symbols]

        # Trier par contribution décroissante
        sorted_data = sorted(
            zip(symbols, absolutes, percentages), key=lambda x: x[1], reverse=True
        )
        symbols, absolutes, percentages = zip(*sorted_data)

        # Couleurs selon contribution (vert si positif, rouge si négatif)
        colors = ["#2ecc71" if abs_val > 0 else "#e74c3c" for abs_val in absolutes]

        # Créer bar chart
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=list(symbols),
                y=list(absolutes),
                text=[f"{pct:.1f}%" for pct in percentages],
                textposition="outside",
                marker_color=colors,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "P&L: $%{y:,.2f}<br>"
                    "Contribution: %{text}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Layout
        fig.update_layout(
            title={
                "text": "💰 Contributions au P&L Total",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="Symbole",
            yaxis_title="P&L Absolu ($)",
            template="plotly_white",
            height=500,
            showlegend=False,
        )

        # Format axe Y en dollars
        fig.update_yaxes(tickformat="$,.0f")

        logger.info("✓ Bar chart contributions P&L généré")
        return fig

    def generate_rolling_correlation(
        self,
        returns_data: Dict[str, pd.Series],
        window: int = 60,
        symbol1: str = None,
        symbol2: str = None,
    ) -> go.Figure:
        """
        Génère un graphique de rolling correlation entre deux symboles

        Args:
            returns_data: Dict {symbol: Series de returns}
            window: Fenêtre de rolling (défaut: 60 jours)
            symbol1: Premier symbole (si None, prend le premier)
            symbol2: Deuxième symbole (si None, prend le deuxième)

        Returns:
            Figure Plotly
        """
        if not returns_data or len(returns_data) < 2:
            logger.warning("Pas assez de symboles pour rolling correlation")
            return None

        # Sélectionner symboles
        symbols = list(returns_data.keys())
        if symbol1 is None:
            symbol1 = symbols[0]
        if symbol2 is None:
            symbol2 = symbols[1] if len(symbols) > 1 else symbols[0]

        if symbol1 not in returns_data or symbol2 not in returns_data:
            logger.warning(f"Symboles {symbol1} ou {symbol2} non trouvés")
            return None

        # Calculer rolling correlation
        returns_df = pd.DataFrame(
            {symbol1: returns_data[symbol1], symbol2: returns_data[symbol2]}
        )

        rolling_corr = (
            returns_df[symbol1].rolling(window=window).corr(returns_df[symbol2])
        )

        # Créer graphique
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=rolling_corr.index,
                y=rolling_corr.values,
                mode="lines",
                name=f"{symbol1} vs {symbol2}",
                line=dict(width=2, color="#3498db"),
                fill="tozeroy",
                fillcolor="rgba(52, 152, 219, 0.2)",
                hovertemplate=(
                    "Date: %{x|%Y-%m-%d}<br>"
                    "Correlation: %{y:.3f}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Ajouter ligne de référence à 0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        # Layout
        fig.update_layout(
            title={
                "text": f"🔄 Rolling Correlation ({window} jours): {symbol1} vs {symbol2}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="Date",
            yaxis_title="Correlation",
            template="plotly_white",
            height=400,
            showlegend=False,
            yaxis=dict(range=[-1, 1]),
        )

        logger.info(f"✓ Rolling correlation {symbol1} vs {symbol2} générée")
        return fig

    def generate_all_rolling_correlations(
        self, returns_data: Dict[str, pd.Series], window: int = 60
    ) -> go.Figure:
        """
        Génère toutes les rolling correlations dans un subplot

        Args:
            returns_data: Dict {symbol: Series de returns}
            window: Fenêtre de rolling

        Returns:
            Figure Plotly avec subplots
        """
        if not returns_data or len(returns_data) < 2:
            logger.warning("Pas assez de symboles")
            return None

        symbols = list(returns_data.keys())
        n_symbols = len(symbols)

        # Calculer nombre de paires
        n_pairs = (n_symbols * (n_symbols - 1)) // 2

        # Créer subplots
        rows = (n_pairs + 1) // 2  # 2 graphiques par ligne
        fig = make_subplots(
            rows=rows,
            cols=2,
            subplot_titles=[
                f"{symbols[i]} vs {symbols[j]}"
                for i in range(n_symbols)
                for j in range(i + 1, n_symbols)
            ],
        )

        # Couleurs
        colors = px.colors.qualitative.Set2

        # Générer toutes les paires
        pair_idx = 0
        for i in range(n_symbols):
            for j in range(i + 1, n_symbols):
                symbol1, symbol2 = symbols[i], symbols[j]

                # Calculer rolling correlation
                returns_df = pd.DataFrame(
                    {symbol1: returns_data[symbol1], symbol2: returns_data[symbol2]}
                )
                rolling_corr = (
                    returns_df[symbol1].rolling(window=window).corr(returns_df[symbol2])
                )

                # Position dans subplot
                row = (pair_idx // 2) + 1
                col = (pair_idx % 2) + 1

                # Ajouter trace
                fig.add_trace(
                    go.Scatter(
                        x=rolling_corr.index,
                        y=rolling_corr.values,
                        mode="lines",
                        name=f"{symbol1} vs {symbol2}",
                        line=dict(width=2, color=colors[pair_idx % len(colors)]),
                        showlegend=False,
                        hovertemplate="Corr: %{y:.3f}<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )

                # Ligne de référence
                fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.3,
                    row=row,
                    col=col,
                )

                pair_idx += 1

        # Layout
        fig.update_layout(
            title={
                "text": f"🔄 Rolling Correlations ({window} jours)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            template="plotly_white",
            height=300 * rows,
            showlegend=False,
        )

        # Update axes
        for i in range(1, rows + 1):
            for j in range(1, 3):
                fig.update_yaxes(range=[-1, 1], row=i, col=j)

        logger.info(f"✓ {n_pairs} rolling correlations générées")
        return fig

    def generate_cumulative_returns_comparison(self) -> go.Figure:
        """
        Génère un graphique des returns cumulés (normalisés à 100)

        Returns:
            Figure Plotly
        """
        if not self.daily_returns:
            logger.warning("Pas de daily_returns pour returns cumulés")
            return None

        fig = go.Figure()
        colors = px.colors.qualitative.Set2

        for idx, (symbol, returns) in enumerate(self.daily_returns.items()):
            # Calculer returns cumulés (base 100)
            cumulative = (1 + returns).cumprod() * 100

            color = colors[idx % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=cumulative.index,
                    y=cumulative.values,
                    mode="lines",
                    name=symbol,
                    line=dict(width=2, color=color),
                    hovertemplate=(
                        f"<b>{symbol}</b><br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        "Value: %{y:.2f}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Ligne de référence à 100
        if self.daily_returns:
            first_series = next(iter(self.daily_returns.values()))
            fig.add_hline(
                y=100,
                line_dash="dash",
                line_color="gray",
                opacity=0.5,
                annotation_text="Base: 100",
            )

        # Layout
        fig.update_layout(
            title={
                "text": "📈 Returns Cumulés Comparés (Base 100)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2c3e50"},
            },
            xaxis_title="Date",
            yaxis_title="Valeur (Base 100)",
            hovermode="x unified",
            template="plotly_white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=500,
        )

        logger.info("✓ Returns cumulés comparés générés")
        return fig

    def generate_all_charts(self) -> Dict[str, go.Figure]:
        """
        Génère tous les graphiques disponibles

        Returns:
            Dict {chart_name: figure}
        """
        logger.info("Génération de tous les graphiques...")

        charts = {}

        # 1. Equity curves
        if self.daily_values:
            charts["equity_curves"] = self.generate_equity_curves()

        # 2. Cumulative returns
        if self.daily_returns:
            charts["cumulative_returns"] = self.generate_cumulative_returns_comparison()

        # 3. Correlation heatmap
        if self.daily_returns:
            charts["correlation_heatmap"] = self.generate_correlation_heatmap(
                self.daily_returns
            )

        # 4. Return vs Drawdown scatter
        if self.by_symbol:
            charts["return_vs_drawdown"] = self.generate_return_vs_drawdown_scatter()

        # 5. P&L contributions
        if self.aggregated.get("pnl_contributions"):
            charts["pnl_contributions"] = self.generate_pnl_contributions_bar()

        # 6. Rolling correlations
        if self.daily_returns and len(self.daily_returns) >= 2:
            charts["rolling_correlations"] = self.generate_all_rolling_correlations(
                self.daily_returns
            )

        logger.info(f"✓ {len(charts)} graphiques générés")

        return charts
