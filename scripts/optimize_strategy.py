#!/usr/bin/env python3
"""
Optimisation des paramètres d'une stratégie
Teste différentes combinaisons pour trouver les meilleurs paramètres
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backtrader as bt
import pandas as pd
from itertools import product
from datetime import datetime

from config import settings
from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger

logger = setup_logger("optimizer")


class StrategyOptimizer:
    """Optimise les paramètres d'une stratégie"""

    def __init__(self, strategy_class, symbols, start_date, end_date, capital=100000):
        self.strategy_class = strategy_class
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.capital = capital
        self.data_handler = DataHandler()
        self.results = []

    def optimize(self, param_grid):
        """
        Optimise les paramètres

        Args:
            param_grid: Dict de paramètres à tester
                       Ex: {'ma_period': [10, 20, 30], 'rsi_period': [7, 14, 21]}
        """
        # Générer toutes les combinaisons
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        total = len(combinations)
        logger.info(f"🔬 Optimisation: {total} combinaisons à tester")

        for i, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))

            logger.info(f"\n[{i}/{total}] Test: {params}")

            # Exécuter le backtest avec ces paramètres
            result = self._run_backtest(params)

            if result:
                self.results.append(
                    {
                        **params,
                        "sharpe": result["sharpe"],
                        "return": result["return"],
                        "drawdown": result["drawdown"],
                        "trades": result["trades"],
                        "win_rate": result["win_rate"],
                    }
                )

        return self._analyze_results()

    def _run_backtest(self, params):
        """Exécute un backtest avec les paramètres donnés"""
        try:
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(self.capital)
            cerebro.broker.setcommission(commission=settings.COMMISSION)

            # Charger les données
            for symbol in self.symbols:
                df = self.data_handler.fetch_data(
                    symbol, self.start_date, self.end_date
                )
                if df is not None and not df.empty:
                    data_feed = create_data_feed(df, name=symbol)
                    cerebro.adddata(data_feed, name=symbol)

            # Ajouter la stratégie avec les paramètres
            cerebro.addstrategy(self.strategy_class, **params, printlog=False)

            # Analyseurs
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

            # Exécuter
            start_value = cerebro.broker.getvalue()
            strategies = cerebro.run()
            end_value = cerebro.broker.getvalue()

            # Récupérer les résultats
            strat = strategies[0]
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()

            total_trades = trades.get("total", {}).get("total", 0)
            won_trades = trades.get("won", {}).get("total", 0)

            return {
                "sharpe": sharpe.get("sharperatio", 0) or 0,
                "return": ((end_value - start_value) / start_value) * 100,
                "drawdown": drawdown.get("max", {}).get("drawdown", 0),
                "trades": total_trades,
                "win_rate": (
                    (won_trades / total_trades * 100) if total_trades > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"Erreur: {e}")
            return None

    def _analyze_results(self):
        """Analyse et affiche les meilleurs résultats"""
        if not self.results:
            logger.error("Aucun résultat")
            return None

        # Convertir en DataFrame
        df = pd.DataFrame(self.results)

        # Trier par Sharpe Ratio
        df_sorted = df.sort_values("sharpe", ascending=False)

        print("\n" + "=" * 80)
        print("🏆 TOP 10 MEILLEURES COMBINAISONS")
        print("=" * 80)

        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        print(df_sorted.head(10).to_string(index=False))

        # Meilleure combinaison
        best = df_sorted.iloc[0].to_dict()

        print("\n" + "=" * 80)
        print("⭐ MEILLEURE COMBINAISON")
        print("=" * 80)
        for key, value in best.items():
            if key in ["sharpe", "return", "drawdown", "win_rate"]:
                print(f"{key:.<30} {value:.2f}")
            else:
                print(f"{key:.<30} {value}")

        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = settings.RESULTS_DIR / f"optimization_{timestamp}.csv"
        df_sorted.to_csv(results_file, index=False)

        logger.info(f"\n✅ Résultats sauvegardés: {results_file}")

        return best


def main():
    """Exemple d'utilisation"""

    print(
        """
╔═══════════════════════════════════════════════════════════════════════╗
║              🔬 OPTIMISEUR DE STRATÉGIE 🔬                           ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    )

    # Exemple: Optimiser MaSuperStrategie
    from strategies.marsi import MaSuperStrategie
    from strategies.moving_average import MovingAverageStrategy

    optimizer = StrategyOptimizer(
        strategy_class=MovingAverageStrategy,
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"],
        start_date="2022-01-01",
        end_date="2024-01-01",
        capital=100000,
    )

    # Définir la grille de paramètres à tester
    param_grid = {
        # 'ma_period': [10, 20, 30, 50],
        # 'rsi_period': [7, 14, 21],
        # 'stop_loss_pct': [0.015, 0.02, 0.025],
        "fast_period": [5 * i for i in range(1, 11)],
        "slow_period": [50 * i for i in range(1, 6)],
    }

    # Optimiser
    best_params = optimizer.optimize(param_grid)

    if best_params:
        print("\n🎯 Utilisez ces paramètres optimaux dans votre stratégie !")


if __name__ == "__main__":
    main()
