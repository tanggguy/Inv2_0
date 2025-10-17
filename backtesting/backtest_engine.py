"""
Moteur de backtesting principal
"""

import backtrader as bt
from datetime import datetime
import pandas as pd
import importlib
import os
from pathlib import Path
from config import settings
from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger
from backtesting.performance_analyzer import PerformanceAnalyzer

logger = setup_logger("backtest_engine")


class BacktestEngine:
    """Moteur principal pour exécuter les backtests"""

    def __init__(
        self,
        strategy_name,
        symbols,
        start_date,
        end_date,
        initial_capital=100000,
        verbose=False,
    ):
        """
        Initialise le moteur de backtesting

        Args:
            strategy_name: Nom de la stratégie à tester
            symbols: Liste des symboles
            start_date: Date de début
            end_date: Date de fin
            initial_capital: Capital initial
            verbose: Mode verbeux
        """
        self.strategy_name = strategy_name
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.verbose = verbose

        # Initialiser Cerebro
        self.cerebro = bt.Cerebro()

        # Paramètres de base
        self.cerebro.broker.setcash(initial_capital)
        self.cerebro.broker.setcommission(commission=settings.COMMISSION)

        # Ajouter les analyseurs
        # Récupérer les analyseurs
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual_returns")
        self.cerebro.addanalyzer(bt.analyzers.Calmar, _name="calmar")
        self.cerebro.addanalyzer(
            bt.analyzers.VWR, _name="vwr"
        )  # Variability-Weighted Return

        self.results = None
        self.data_handler = DataHandler()

    def _load_strategy(self):
        """Charge la stratégie dynamiquement"""

        try:
            # Liste des stratégies hardcodées (compatibilité)
            hardcoded_strategies = {
                "MovingAverage": ("strategies.moving_average", "MovingAverageStrategy"),
                "RSI": ("strategies.rsi_strategy", "RSIStrategy"),
                "MACrossoverAdvanced": (
                    "strategies.advanced_strategies",
                    "MACrossoverAdvanced",
                ),
                "RSITrailingStop": ("strategies.rsitrailingstop", "RSITrailingStop"),
                "BreakoutATRStop": (
                    "strategies.advanced_strategies",
                    "BreakoutATRStop",
                ),
                "MomentumMultipleStops": (
                    "strategies.advanced_strategies",
                    "MomentumMultipleStops",
                ),
                "MaRSI": ("strategies.marsi", "MaRSI"),
                "BollingerBandsStrategy": (
                    "strategies.bollingerbands",
                    "BollingerBandsStrategy",
                ),
                "MeanReversionStrategy": (
                    "strategies.bollingerbands",
                    "MeanReversionStrategy",
                ),
                "SqueezeMomentumStrategy": (
                    "strategies.squeezemomentumstrategy",
                    "SqueezeMomentumStrategy",
                ),
            }

            # Vérifier d'abord les stratégies hardcodées
            if self.strategy_name in hardcoded_strategies:
                module_name, class_name = hardcoded_strategies[self.strategy_name]
                module = importlib.import_module(module_name)
                return getattr(module, class_name)

            # Sinon, chercher dynamiquement dans le dossier strategies
            strategies_dir = Path("strategies")

            # Parcourir tous les fichiers .py
            for strategy_file in strategies_dir.glob("*.py"):
                if strategy_file.name.startswith("__"):
                    continue

                # Convertir le nom de fichier en nom de module
                module_name = f"strategies.{strategy_file.stem}"

                try:
                    # Importer le module
                    module = importlib.import_module(module_name)

                    # Chercher une classe qui correspond au nom
                    if hasattr(module, self.strategy_name):
                        strategy_class = getattr(module, self.strategy_name)
                        logger.info(
                            f"✓ Stratégie '{self.strategy_name}' chargée depuis {strategy_file.name}"
                        )
                        return strategy_class

                except ImportError as e:
                    logger.debug(f"Impossible d'importer {module_name}: {e}")
                    continue

            # Si rien n'est trouvé
            logger.error(f"Stratégie '{self.strategy_name}' introuvable")
            logger.info("Stratégies disponibles dans le dossier strategies/:")

            # Lister les stratégies disponibles
            for strategy_file in strategies_dir.glob("*.py"):
                if strategy_file.name.startswith("__"):
                    continue
                logger.info(f"  - {strategy_file.stem}")

            return None

        except Exception as e:
            logger.error(f"Erreur lors du chargement de la stratégie: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _load_data(self):
        """Charge les données pour tous les symboles"""
        logger.info(f"Chargement des données pour {len(self.symbols)} symboles...")

        for symbol in self.symbols:
            df = self.data_handler.fetch_data(symbol, self.start_date, self.end_date)

            if df is not None and not df.empty:
                data_feed = create_data_feed(df, name=symbol)
                self.cerebro.adddata(data_feed, name=symbol)
                logger.info(f"✓ Données ajoutées: {symbol}")
            else:
                logger.warning(f"⚠ Données manquantes: {symbol}")

    def run(self):
        """Exécute le backtest"""
        logger.info("Démarrage du backtest...")

        # Charger la stratégie
        strategy_class = self._load_strategy()
        if strategy_class is None:
            return None

        self.cerebro.addstrategy(strategy_class)

        # Charger les données
        self._load_data()

        # Valeur initiale
        start_value = self.cerebro.broker.getvalue()
        logger.info(f"Valeur initiale du portefeuille: ${start_value:,.2f}")

        # Exécuter
        try:
            strategies = self.cerebro.run()
            self.strategy_instance = strategies[0]
        except Exception as e:
            logger.error(f"Erreur pendant l'exécution: {e}", exc_info=True)
            return None

        # Valeur finale
        end_value = self.cerebro.broker.getvalue()
        logger.info(f"Valeur finale du portefeuille: ${end_value:,.2f}")

        # Analyser les résultats
        return self._analyze_results(start_value, end_value)

    def _analyze_results(self, start_value, end_value):
        """Analyse les résultats du backtest"""
        try:

            sharpe = self.strategy_instance.analyzers.sharpe.get_analysis()
            drawdown = self.strategy_instance.analyzers.drawdown.get_analysis()
            returns_data = self.strategy_instance.analyzers.returns.get_analysis()
            trades = self.strategy_instance.analyzers.trades.get_analysis()

            calmar = self.strategy_instance.analyzers.calmar.get_analysis()
            vwr = self.strategy_instance.analyzers.vwr.get_analysis()

            total_return_pct = returns_data.get("rtot", 0) * 100
            annual_returns_pct = returns_data.get("rnorm100", 0)
            # Nombre de trades
            total_trades = trades.get("total", {}).get("total", 0)
            won_trades = trades.get("won", {}).get("total", 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

            calmar_ratio = calmar.get("calmar", 0)
            if calmar_ratio == 0 and annual_returns_pct > 0:
                max_dd = drawdown.get("max", {}).get("drawdown", 0)
                if max_dd > 0:
                    calmar_ratio = annual_returns_pct / max_dd
            results = {
                "initial_value": start_value,
                "final_value": end_value,
                "total_return": total_return_pct,
                "annual_return": annual_returns_pct,
                "sharpe_ratio": sharpe.get("sharperatio", 0),
                "max_drawdown": drawdown.get("max", {}).get("drawdown", 0),
                "calmar_ratio": calmar_ratio,
                "vwr": vwr.get("vwr", 0),
                "total_trades": total_trades,
                "won_trades": won_trades,
                "lost_trades": trades.get("lost", {}).get("total", 0),
                "win_rate": win_rate,
                "avg_win": trades.get("won", {}).get("pnl", {}).get("average", 0),
                "avg_loss": trades.get("lost", {}).get("pnl", {}).get("average", 0),
            }

            self.results = results
            return results

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
            return None

    def plot_results(self):
        """Affiche les graphiques"""
        try:
            self.cerebro.plot(style="candlestick", barup="green", bardown="red")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage: {e}")

    def generate_report(self):
        """Génère un rapport détaillé"""
        if self.results is None:
            logger.error("Aucun résultat à reporter")
            return None

        analyzer = PerformanceAnalyzer(self.results, self.strategy_name)
        report_path = analyzer.generate_report()

        return report_path
