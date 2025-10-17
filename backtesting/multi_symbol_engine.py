"""
Multi-Symbol Backtest Engine

Moteur de backtesting pour trader plusieurs symboles simultanément
avec des sous-portefeuilles séparés.

Architecture:
- Hérite de BacktestEngine pour compatibilité
- Lance un backtest indépendant par symbole
- Agrège les résultats globaux
- Applique les contraintes de positions
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from backtesting.backtest_engine import BacktestEngine
from backtesting.portfolio_manager import PortfolioManager
from monitoring.logger import setup_logger

logger = setup_logger("multi_symbol_engine")


class MultiSymbolBacktestEngine(BacktestEngine):
    """
    Moteur de backtesting multi-symbole avec portfolios séparés

    Différences avec BacktestEngine:
    - Lance N backtests en parallèle (1 par symbole)
    - Chaque symbole a son capital alloué
    - Agrège les résultats finaux
    - Applique contraintes multi-symboles
    """

    def __init__(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000,
        symbol_weights: Optional[Dict[str, float]] = None,
        max_positions: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialise le moteur multi-symbole

        Args:
            strategy_name: Nom de la stratégie
            symbols: Liste des symboles à trader
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)
            initial_capital: Capital total du portefeuille
            symbol_weights: Dict des poids {symbol: weight}
                           Si None, equal-weight
            max_positions: Nombre max de positions simultanées
            verbose: Mode verbeux
        """
        # Initialiser le parent (BacktestEngine)
        super().__init__(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            verbose=verbose,
        )

        # Initialiser le gestionnaire de portefeuille
        self.portfolio_manager = PortfolioManager(
            symbols=symbols,
            total_capital=initial_capital,
            weights=symbol_weights,
            max_positions=max_positions,
        )

        # Résultats par symbole
        self.symbol_results = {}

        # Résultats agrégés
        self.aggregated_results = None

        # Séries temporelles de returns (pour corrélations)
        self.daily_returns = {}  # {symbol: pd.Series}
        self.daily_values = {}  # {symbol: pd.Series}

        logger.info(
            f"MultiSymbolBacktestEngine initialisé: "
            f"{len(symbols)} symboles, "
            f"capital ${initial_capital:,.0f}"
        )

    def run(self) -> Dict:
        """
        Lance le backtest multi-symbole

        Process:
        1. Lance un backtest par symbole avec son capital alloué
        2. Collecte les résultats de chaque symbole
        3. Agrège les résultats globaux
        4. Retourne résultats complets

        Returns:
            Dict avec résultats agrégés + résultats par symbole
        """
        logger.info("=" * 80)
        logger.info("🚀 DÉMARRAGE BACKTEST MULTI-SYMBOLE")
        logger.info("=" * 80)
        logger.info(f"Stratégie: {self.strategy_name}")
        logger.info(f"Symboles: {', '.join(self.symbols)}")
        logger.info(f"Période: {self.start_date} → {self.end_date}")
        logger.info(f"Capital total: ${self.initial_capital:,.2f}")
        logger.info("=" * 80)

        # Lancer les backtests par symbole
        self.symbol_results = self._run_all_symbol_backtests()

        # Vérifier qu'on a des résultats
        if not self.symbol_results:
            logger.error("Aucun résultat de backtest disponible")
            return None

        # Agréger les résultats
        self.aggregated_results = self._aggregate_results()

        # Afficher résumé
        self._print_summary()

        # Retourner résultats complets
        return {
            "aggregated": self.aggregated_results,
            "by_symbol": self.symbol_results,
            "portfolio_info": self.portfolio_manager.get_summary(),
            "daily_returns": self.daily_returns,  # Ajout pour corrélations
            "daily_values": self.daily_values,  # Ajout pour visualisations
        }

    def _run_all_symbol_backtests(self) -> Dict[str, Dict]:
        """
        Lance tous les backtests de symboles

        Stratégie:
        - Lance les backtests en parallèle pour accélérer
        - Utilise ThreadPoolExecutor
        - Chaque symbole dans son thread

        Returns:
            Dict {symbol: backtest_results}
        """
        logger.info(f"\n📊 Lancement de {len(self.symbols)} backtests...")

        results = {}

        # Mode séquentiel pour debug si verbose
        if self.verbose:
            logger.info("Mode séquentiel (verbose activé)")
            for symbol in self.symbols:
                result = self._run_symbol_backtest(symbol)
                if result:
                    results[symbol] = result
        else:
            # Mode parallèle pour performance
            logger.info("Mode parallèle (max 4 threads)")
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Soumettre tous les jobs
                future_to_symbol = {
                    executor.submit(self._run_symbol_backtest, symbol): symbol
                    for symbol in self.symbols
                }

                # Collecter les résultats
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if result:
                            results[symbol] = result
                            logger.info(f"✓ {symbol} terminé")
                    except Exception as e:
                        logger.error(f"✗ Erreur {symbol}: {e}")

        logger.info(f"✓ {len(results)}/{len(self.symbols)} backtests réussis\n")

        return results

    def _run_symbol_backtest(self, symbol: str) -> Optional[Dict]:
        """
        Lance un backtest pour UN symbole avec son capital alloué

        Args:
            symbol: Symbole à trader

        Returns:
            Dict avec résultats du backtest ou None si erreur
        """
        try:
            # Obtenir le capital alloué
            allocated_capital = self.portfolio_manager.get_allocation(symbol)
            weight = self.portfolio_manager.get_weight(symbol)

            logger.info(
                f"Backtest {symbol}: " f"${allocated_capital:,.2f} ({weight:.1%})"
            )

            # Créer un cerebro dédié pour ce symbole
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(allocated_capital)
            cerebro.broker.setcommission(commission=0.001)

            # Charger les données pour ce symbole uniquement
            df = self.data_handler.fetch_data(symbol, self.start_date, self.end_date)

            if df is None or df.empty:
                logger.warning(f"Pas de données pour {symbol}")
                return None

            # Créer le data feed
            from data.data_fetcher import create_data_feed

            data_feed = create_data_feed(df, name=symbol)
            cerebro.adddata(data_feed, name=symbol)

            # Charger la stratégie
            strategy_class = self._load_strategy()
            if strategy_class is None:
                logger.error(f"Impossible de charger stratégie pour {symbol}")
                return None

            cerebro.addstrategy(strategy_class, printlog=False)

            # Ajouter analyzer TimeReturn pour collecter returns quotidiens
            cerebro.addanalyzer(
                bt.analyzers.TimeReturn,
                _name="time_return",
                timeframe=bt.TimeFrame.Days,
            )

            # Ajouter les analyseurs standards
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
            cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual_returns")

            # Exécuter
            start_value = cerebro.broker.getvalue()
            strategies = cerebro.run()
            end_value = cerebro.broker.getvalue()

            # Collecter les returns quotidiens depuis TimeReturn analyzer
            if strategies:
                self._collect_daily_returns_from_analyzer(strategies[0], symbol)

            # Analyser résultats
            if not strategies:
                logger.warning(f"Pas de stratégie exécutée pour {symbol}")
                return None

            strategy_instance = strategies[0]
            results = self._analyze_symbol_results(
                strategy_instance,
                start_value,
                end_value,
                symbol,
                allocated_capital,
                weight,
            )

            return results

        except Exception as e:
            logger.error(f"Erreur backtest {symbol}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _analyze_symbol_results(
        self,
        strategy_instance,
        start_value: float,
        end_value: float,
        symbol: str,
        allocated_capital: float,
        weight: float,
    ) -> Dict:
        """
        Analyse les résultats d'un backtest symbole

        Args:
            strategy_instance: Instance de la stratégie exécutée
            start_value: Valeur initiale
            end_value: Valeur finale
            symbol: Symbole tradé
            allocated_capital: Capital alloué
            weight: Poids du symbole

        Returns:
            Dict avec toutes les métriques
        """
        # Récupérer les analyseurs
        sharpe_analysis = strategy_instance.analyzers.sharpe.get_analysis()
        drawdown_analysis = strategy_instance.analyzers.drawdown.get_analysis()
        trades_analysis = strategy_instance.analyzers.trades.get_analysis()

        # Métriques de base
        total_return = ((end_value - start_value) / start_value) * 100
        sharpe_ratio = sharpe_analysis.get("sharperatio", 0) or 0
        max_drawdown = drawdown_analysis.get("max", {}).get("drawdown", 0) or 0

        # Métriques de trading
        total_trades = trades_analysis.get("total", {}).get("total", 0)
        won_trades = trades_analysis.get("won", {}).get("total", 0)
        lost_trades = trades_analysis.get("lost", {}).get("total", 0)

        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L
        absolute_pnl = end_value - start_value

        results = {
            # Identification
            "symbol": symbol,
            "allocated_capital": allocated_capital,
            "weight": weight,
            # Performance
            "initial_value": start_value,
            "final_value": end_value,
            "absolute_pnl": absolute_pnl,
            "total_return": total_return,
            # Métriques de risque
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            # Métriques de trading
            "total_trades": total_trades,
            "won_trades": won_trades,
            "lost_trades": lost_trades,
            "win_rate": win_rate,
        }

        return results

    def _aggregate_results(self) -> Dict:
        """
        Agrège les résultats de tous les symboles

        Calcule:
        - Performance globale du portefeuille
        - Métriques agrégées
        - Contribution de chaque symbole

        Returns:
            Dict avec résultats agrégés
        """
        logger.info("📊 Agrégation des résultats...")

        # Valeurs totales
        total_initial = sum(r["initial_value"] for r in self.symbol_results.values())
        total_final = sum(r["final_value"] for r in self.symbol_results.values())
        total_pnl = total_final - total_initial

        # Return global
        portfolio_return = (total_pnl / total_initial) * 100

        # Sharpe moyen pondéré par le capital
        weighted_sharpe = sum(
            r["sharpe_ratio"] * r["weight"] for r in self.symbol_results.values()
        )

        # Max drawdown (pire des symboles)
        max_portfolio_drawdown = min(
            r["max_drawdown"] for r in self.symbol_results.values()
        )

        # Trades totaux
        total_trades = sum(r["total_trades"] for r in self.symbol_results.values())
        total_won = sum(r["won_trades"] for r in self.symbol_results.values())
        total_lost = sum(r["lost_trades"] for r in self.symbol_results.values())

        portfolio_win_rate = (total_won / total_trades * 100) if total_trades > 0 else 0

        # Contribution P&L par symbole
        pnl_contributions = {}
        for symbol, results in self.symbol_results.items():
            contrib_pct = (
                (results["absolute_pnl"] / total_pnl * 100) if total_pnl != 0 else 0
            )
            pnl_contributions[symbol] = {
                "absolute": results["absolute_pnl"],
                "percentage": contrib_pct,
            }

        aggregated = {
            # Performance globale
            "initial_value": total_initial,
            "final_value": total_final,
            "absolute_pnl": total_pnl,
            "portfolio_return": portfolio_return,
            # Métriques de risque
            "portfolio_sharpe": weighted_sharpe,
            "portfolio_max_drawdown": max_portfolio_drawdown,
            # Trading
            "total_trades": total_trades,
            "won_trades": total_won,
            "lost_trades": total_lost,
            "portfolio_win_rate": portfolio_win_rate,
            # Contributions
            "pnl_contributions": pnl_contributions,
            # Metadata
            "strategy": self.strategy_name,
            "symbols": self.symbols,
            "period": {"start": self.start_date, "end": self.end_date},
            "timestamp": datetime.now().isoformat(),
        }

        return aggregated

    def _print_summary(self) -> None:
        """Affiche un résumé des résultats"""
        agg = self.aggregated_results

        logger.info("\n" + "=" * 80)
        logger.info("📈 RÉSULTATS PAR SYMBOLE")
        logger.info("=" * 80)
        logger.info(
            f"{'Symbol':<8} {'Return':>10} {'Sharpe':>8} {'DD':>8} "
            f"{'Trades':>8} {'Win%':>8}"
        )
        logger.info("-" * 80)

        for symbol in sorted(self.symbols):
            if symbol not in self.symbol_results:
                continue

            r = self.symbol_results[symbol]
            logger.info(
                f"{symbol:<8} "
                f"{r['total_return']:>9.2f}% "
                f"{r['sharpe_ratio']:>8.2f} "
                f"{r['max_drawdown']:>7.1f}% "
                f"{r['total_trades']:>8} "
                f"{r['win_rate']:>7.1f}%"
            )

        logger.info("=" * 80)
        logger.info("📊 PERFORMANCE GLOBALE DU PORTFOLIO")
        logger.info("=" * 80)
        logger.info(f"Return Total:          {agg['portfolio_return']:>8.2f}%")
        logger.info(f"Sharpe Ratio:          {agg['portfolio_sharpe']:>8.2f}")
        logger.info(f"Max Drawdown:          {agg['portfolio_max_drawdown']:>7.1f}%")
        logger.info(f"Total Trades:          {agg['total_trades']:>8}")
        logger.info(f"Win Rate Global:       {agg['portfolio_win_rate']:>7.1f}%")
        logger.info("-" * 80)
        logger.info(f"P&L Total:             ${agg['absolute_pnl']:>12,.2f}")
        logger.info(f"Valeur Initiale:       ${agg['initial_value']:>12,.2f}")
        logger.info(f"Valeur Finale:         ${agg['final_value']:>12,.2f}")
        logger.info("=" * 80)

        logger.info("\n💰 CONTRIBUTION AU P&L")
        logger.info("-" * 80)
        for symbol in sorted(self.symbols):
            if symbol not in agg["pnl_contributions"]:
                continue
            contrib = agg["pnl_contributions"][symbol]
            logger.info(
                f"{symbol:<8}: {contrib['percentage']:>6.1f}%  "
                f"(${contrib['absolute']:>10,.2f})"
            )
        logger.info("=" * 80 + "\n")

    def _collect_daily_returns_from_analyzer(self, strategy, symbol: str):
        """
        Collecte les returns quotidiens depuis TimeReturn analyzer

        Args:
            strategy: Instance de stratégie avec analyzers
            symbol: Symbole concerné
        """
        try:
            # Récupérer l'analyzer TimeReturn
            time_return = strategy.analyzers.time_return.get_analysis()

            if not time_return:
                logger.warning(f"Pas de returns collectés pour {symbol}")
                return

            # Convertir en Series pandas
            # time_return est un OrderedDict {date: return_value}
            dates = list(time_return.keys())
            returns = list(time_return.values())

            if not dates or not returns:
                logger.warning(f"Returns vides pour {symbol}")
                return

            # Créer Series de returns
            self.daily_returns[symbol] = pd.Series(
                returns, index=pd.DatetimeIndex(dates), name=symbol
            )

            # Calculer valeurs cumulées pour daily_values
            # cumulative_value = initial_capital * (1 + return).cumprod()
            allocated_capital = self.portfolio_manager.get_allocation(symbol)
            cumulative_returns = (1 + self.daily_returns[symbol]).cumprod()
            self.daily_values[symbol] = allocated_capital * cumulative_returns

            logger.info(f"✓ Collecté {len(returns)} returns quotidiens pour {symbol}")

        except Exception as e:
            logger.error(f"Erreur collecte returns {symbol}: {e}")
            import traceback

            traceback.print_exc()

    def get_daily_returns(self) -> Dict[str, pd.Series]:
        """
        Retourne les returns quotidiens de tous les symboles

        Returns:
            Dict {symbol: Series de returns quotidiens}
        """
        return self.daily_returns.copy()

    def get_daily_values(self) -> Dict[str, pd.Series]:
        """
        Retourne les valeurs quotidiennes de tous les symboles

        Returns:
            Dict {symbol: Series de valeurs quotidiennes}
        """
        return self.daily_values.copy()

    def get_results(self) -> Dict:
        """
        Retourne les résultats complets

        Returns:
            Dict avec résultats agrégés + par symbole + returns
        """
        return {
            "aggregated": self.aggregated_results,
            "by_symbol": self.symbol_results,
            "portfolio_info": self.portfolio_manager.get_summary(),
            "daily_returns": self.daily_returns,  # Ajout pour corrélations
            "daily_values": self.daily_values,  # Ajout pour visualisations
        }
