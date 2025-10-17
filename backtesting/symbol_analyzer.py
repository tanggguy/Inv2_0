"""
Symbol Analyzer - Analyses avancées multi-symbole

Ce module fournit:
- Métriques détaillées par symbole
- Matrice de corrélation entre symboles
- Contribution P&L par symbole
- Diversification ratio
- Statistiques comparatives
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from scipy import stats
from monitoring.logger import setup_logger

logger = setup_logger("symbol_analyzer")


class SymbolAnalyzer:
    """
    Analyseur avancé pour backtests multi-symboles

    Fonctionnalités:
    - Métriques par symbole (Sharpe, Return, DD, etc.)
    - Corrélations entre symboles
    - Contribution au P&L
    - Diversification du portefeuille
    """

    def __init__(self, symbol_results: Dict[str, Dict]):
        """
        Initialise l'analyseur

        Args:
            symbol_results: Dict {symbol: backtest_results}
        """
        self.symbol_results = symbol_results
        self.symbols = list(symbol_results.keys())

        logger.info(f"SymbolAnalyzer initialisé avec {len(self.symbols)} symboles")

    def get_metrics_dataframe(self) -> pd.DataFrame:
        """
        Retourne un DataFrame avec toutes les métriques par symbole

        Returns:
            DataFrame avec une ligne par symbole et colonnes de métriques
        """
        rows = []

        for symbol, results in self.symbol_results.items():
            row = {
                "symbol": symbol,
                "allocated_capital": results["allocated_capital"],
                "weight": results["weight"],
                "return_pct": results["total_return"],
                "sharpe_ratio": results["sharpe_ratio"],
                "max_drawdown": results["max_drawdown"],
                "total_trades": results["total_trades"],
                "win_rate": results["win_rate"],
                "absolute_pnl": results["absolute_pnl"],
                "final_value": results["final_value"],
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # Trier par return décroissant
        df = df.sort_values("return_pct", ascending=False).reset_index(drop=True)

        return df

    def calculate_correlation_matrix(
        self, returns_data: Dict[str, pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calcule la matrice de corrélation entre les symboles

        Args:
            returns_data: Dict {symbol: Series de returns quotidiens}
                         Si None, retourne matrice identité (placeholder)

        Returns:
            DataFrame matrice de corrélation (N x N)
        """
        if returns_data is None or not returns_data:
            # Matrice identité (placeholder)
            n_symbols = len(self.symbols)
            corr_matrix = pd.DataFrame(
                np.eye(n_symbols), index=self.symbols, columns=self.symbols
            )

            logger.warning(
                "Corrélation basée sur matrice identité. "
                "Fournir returns_data pour calculs réels."
            )
            return corr_matrix

        # Vraie matrice de corrélation
        returns_df = pd.DataFrame(returns_data)
        corr_matrix = returns_df.corr()

        # Calculer corrélation moyenne
        # Extraire triangulaire supérieure sans diagonale
        n = len(corr_matrix)
        upper_triangle = []
        for i in range(n):
            for j in range(i + 1, n):
                upper_triangle.append(corr_matrix.iloc[i, j])

        if upper_triangle:
            avg_corr = np.mean(upper_triangle)
            logger.info(
                f"Matrice de corrélation calculée (corr. moyenne: {avg_corr:.2f})"
            )
        else:
            logger.info("Matrice de corrélation calculée")

        return corr_matrix

    def calculate_pnl_contributions(self) -> Dict[str, Dict]:
        """
        Calcule la contribution de chaque symbole au P&L total

        Returns:
            Dict {symbol: {'absolute': X, 'percentage': Y}}
        """
        # P&L total du portfolio
        total_pnl = sum(r["absolute_pnl"] for r in self.symbol_results.values())

        contributions = {}

        for symbol, results in self.symbol_results.items():
            pnl = results["absolute_pnl"]
            contrib_pct = (pnl / total_pnl * 100) if total_pnl != 0 else 0

            contributions[symbol] = {"absolute": pnl, "percentage": contrib_pct}

        return contributions

    def calculate_diversification_ratio(
        self, returns_data: Dict[str, pd.Series] = None
    ) -> float:
        """
        Calcule le ratio de diversification du portefeuille

        Diversification Ratio = (Somme des vols pondérés) / (Vol du portfolio)

        Plus le ratio est élevé, plus le portfolio est diversifié.
        Ratio = 1.0 → pas de diversification
        Ratio > 1.0 → diversification bénéfique

        Args:
            returns_data: Dict {symbol: Series de returns quotidiens}
                         Si None, utilise proxy avec drawdowns

        Returns:
            Diversification ratio (float)
        """
        if returns_data is None or not returns_data:
            # Calcul simplifié avec drawdowns comme proxy
            weights = []
            volatilities = []

            for symbol in self.symbols:
                results = self.symbol_results[symbol]
                weight = results["weight"]
                vol = abs(results["max_drawdown"])

                weights.append(weight)
                volatilities.append(vol)

            weights = np.array(weights)
            volatilities = np.array(volatilities)

            weighted_vol_sum = np.sum(weights * volatilities)
            portfolio_vol = np.sum(weights * volatilities)

            if portfolio_vol > 0:
                div_ratio = weighted_vol_sum / portfolio_vol
            else:
                div_ratio = 1.0

            logger.info(f"Diversification ratio (simplifié): {div_ratio:.2f}")
            return div_ratio

        # Vrai calcul avec returns
        returns_df = pd.DataFrame(returns_data)

        # Calculer volatilités
        volatilities = returns_df.std()

        # Poids
        weights = np.array(
            [self.symbol_results[sym]["weight"] for sym in returns_df.columns]
        )

        # Matrice de corrélation
        corr_matrix = returns_df.corr().values

        # Somme pondérée des volatilités
        weighted_vol = np.sum(weights * volatilities.values)

        # Volatilité du portfolio
        # Var(portfolio) = w' * Cov * w
        # Cov = Corr * diag(vol) * diag(vol)
        cov_matrix = corr_matrix * np.outer(volatilities.values, volatilities.values)
        portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_var)

        # Ratio
        div_ratio = weighted_vol / portfolio_vol if portfolio_vol > 0 else 1.0

        logger.info(f"Diversification ratio (réel): {div_ratio:.2f}")

        return div_ratio

    def get_top_performers(
        self, n: int = 3, metric: str = "return_pct"
    ) -> pd.DataFrame:
        """
        Retourne les N meilleurs symboles selon une métrique

        Args:
            n: Nombre de top performers
            metric: Métrique de classement
                   ('return_pct', 'sharpe_ratio', 'win_rate')

        Returns:
            DataFrame avec top N symboles
        """
        df = self.get_metrics_dataframe()

        # Trier par métrique décroissante
        df_sorted = df.sort_values(metric, ascending=False)

        return df_sorted.head(n)

    def get_bottom_performers(
        self, n: int = 3, metric: str = "return_pct"
    ) -> pd.DataFrame:
        """
        Retourne les N pires symboles selon une métrique

        Args:
            n: Nombre de bottom performers
            metric: Métrique de classement

        Returns:
            DataFrame avec bottom N symboles
        """
        df = self.get_metrics_dataframe()

        # Trier par métrique croissante
        df_sorted = df.sort_values(metric, ascending=True)

        return df_sorted.head(n)

    def calculate_risk_adjusted_returns(self) -> pd.DataFrame:
        """
        Calcule les returns ajustés au risque pour chaque symbole

        Returns:
            DataFrame avec métriques de risque ajusté
        """
        rows = []

        for symbol, results in self.symbol_results.items():
            ret = results["total_return"]
            dd = abs(results["max_drawdown"])
            sharpe = results["sharpe_ratio"]

            # Calmar Ratio = Return / Max Drawdown
            calmar = ret / dd if dd > 0 else 0

            # Return-to-Drawdown ratio
            ret_to_dd = ret / dd if dd > 0 else 0

            row = {
                "symbol": symbol,
                "return": ret,
                "sharpe_ratio": sharpe,
                "calmar_ratio": calmar,
                "return_to_dd": ret_to_dd,
                "max_drawdown": dd,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df = df.sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)

        return df

    def calculate_trade_efficiency(self) -> pd.DataFrame:
        """
        Calcule l'efficacité du trading par symbole

        Returns:
            DataFrame avec métriques d'efficacité
        """
        rows = []

        for symbol, results in self.symbol_results.items():
            trades = results["total_trades"]
            win_rate = results["win_rate"]
            pnl = results["absolute_pnl"]

            # P&L moyen par trade
            avg_pnl_per_trade = pnl / trades if trades > 0 else 0

            # Efficacité = (Win Rate / 100) * avg_pnl_per_trade
            efficiency = (win_rate / 100) * avg_pnl_per_trade if trades > 0 else 0

            row = {
                "symbol": symbol,
                "total_trades": trades,
                "win_rate": win_rate,
                "avg_pnl_per_trade": avg_pnl_per_trade,
                "efficiency_score": efficiency,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df = df.sort_values("efficiency_score", ascending=False).reset_index(drop=True)

        return df

    def get_summary_statistics(self) -> Dict:
        """
        Retourne des statistiques résumées sur tous les symboles

        Returns:
            Dict avec statistiques agrégées
        """
        df = self.get_metrics_dataframe()

        stats = {
            "count": len(df),
            "return": {
                "mean": df["return_pct"].mean(),
                "std": df["return_pct"].std(),
                "min": df["return_pct"].min(),
                "max": df["return_pct"].max(),
            },
            "sharpe": {
                "mean": df["sharpe_ratio"].mean(),
                "std": df["sharpe_ratio"].std(),
                "min": df["sharpe_ratio"].min(),
                "max": df["sharpe_ratio"].max(),
            },
            "drawdown": {
                "mean": df["max_drawdown"].mean(),
                "worst": df["max_drawdown"].min(),
                "best": df["max_drawdown"].max(),
            },
            "win_rate": {
                "mean": df["win_rate"].mean(),
                "min": df["win_rate"].min(),
                "max": df["win_rate"].max(),
            },
            "trades": {
                "total": df["total_trades"].sum(),
                "mean_per_symbol": df["total_trades"].mean(),
            },
        }

        return stats

    def print_analysis(self) -> None:
        """Affiche une analyse complète formatée"""

        logger.info("\n" + "=" * 80)
        logger.info("📊 ANALYSE DÉTAILLÉE PAR SYMBOLE")
        logger.info("=" * 80)

        # Métriques par symbole
        df = self.get_metrics_dataframe()
        logger.info("\n" + df.to_string(index=False))

        # Top performers
        logger.info("\n🏆 TOP 3 PERFORMERS (Return)")
        logger.info("-" * 80)
        top = self.get_top_performers(3, "return_pct")
        for _, row in top.iterrows():
            logger.info(
                f"{row['symbol']:6s}: {row['return_pct']:>7.2f}%  "
                f"(Sharpe: {row['sharpe_ratio']:.2f})"
            )

        # Contributions P&L
        logger.info("\n💰 CONTRIBUTIONS AU P&L")
        logger.info("-" * 80)
        contributions = self.calculate_pnl_contributions()
        for symbol in sorted(
            self.symbols, key=lambda s: contributions[s]["percentage"], reverse=True
        ):
            contrib = contributions[symbol]
            logger.info(
                f"{symbol:6s}: {contrib['percentage']:>6.1f}%  "
                f"(${contrib['absolute']:>10,.2f})"
            )

        # Statistiques résumées
        logger.info("\n📈 STATISTIQUES RÉSUMÉES")
        logger.info("-" * 80)
        stats = self.get_summary_statistics()
        logger.info(f"Return moyen:      {stats['return']['mean']:>7.2f}%")
        logger.info(f"Sharpe moyen:      {stats['sharpe']['mean']:>7.2f}")
        logger.info(f"Win rate moyen:    {stats['win_rate']['mean']:>6.1f}%")
        logger.info(f"Trades totaux:     {stats['trades']['total']:>7}")

        # Diversification
        div_ratio = self.calculate_diversification_ratio()
        logger.info(f"Diversification:   {div_ratio:>7.2f}")

        logger.info("=" * 80 + "\n")

    def export_to_csv(self, filepath: str) -> None:
        """
        Export les métriques en CSV

        Args:
            filepath: Chemin du fichier CSV
        """
        df = self.get_metrics_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"Métriques exportées vers: {filepath}")

    def export_correlation_matrix(self, filepath: str) -> None:
        """
        Export la matrice de corrélation en CSV

        Args:
            filepath: Chemin du fichier CSV
        """
        corr = self.calculate_correlation_matrix()
        corr.to_csv(filepath)
        logger.info(f"Matrice de corrélation exportée vers: {filepath}")
