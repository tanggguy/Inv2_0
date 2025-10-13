"""
Multi-Strategy Runner - Orchestrateur pour plusieurs stratégies en parallèle
"""

import backtrader as bt
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import importlib
from monitoring.logger import setup_logger

logger = setup_logger("multi_strategy")


class StrategyInstance:
    """Représente une instance de stratégie"""

    def __init__(self, name, config, store, circuit_breaker=None):
        """
        Initialise une instance de stratégie

        Args:
            name: Nom de la stratégie
            config: Configuration de la stratégie
            store: AlpacaStore instance
            circuit_breaker: Circuit breaker (optionnel)
        """
        self.name = name
        self.config = config
        self.store = store
        self.circuit_breaker = circuit_breaker

        # Cerebro pour cette stratégie
        self.cerebro = None
        self.strategy = None
        self.results = None

        # État
        self.running = False
        self.thread = None
        self.performance = {
            "pnl": 0,
            "trades": 0,
            "win_rate": 0,
            "sharpe": 0,
            "drawdown": 0,
            "last_update": None,
        }

        logger.info(f"StrategyInstance créée: {name}")

    def initialize(self):
        """Initialise Cerebro et la stratégie"""
        try:
            # Créer Cerebro
            self.cerebro = bt.Cerebro()

            # Configuration du broker
            broker = self.store.get_broker()
            self.cerebro.setbroker(broker)

            # # Capital initial
            # self.cerebro.broker.setcash(self.config['capital_allocation'])

            # Ajouter les données pour chaque symbole
            for symbol in self.config["symbols"]:
                data = self.store.get_data(
                    symbol=symbol,
                    timeframe=bt.TimeFrame.Minutes,
                    compression=60,
                    historical=True,
                    backfill_days=100,
                )
                self.cerebro.adddata(data, name=symbol)
                logger.info(f"Data ajouté pour {symbol}")

            # Charger la classe de stratégie
            strategy_class = self._load_strategy_class()

            # Ajouter la stratégie avec les paramètres
            params = self.config.get("params", {})
            self.cerebro.addstrategy(strategy_class, **params)

            # Ajouter les analyseurs
            self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

            logger.info(
                f"Stratégie {self.name} initialisée avec ${self.config['capital_allocation']:.2f}"
            )

        except Exception as e:
            logger.error(f"Erreur initialisation stratégie {self.name}: {e}")
            raise

    def _load_strategy_class(self):
        """Charge dynamiquement la classe de stratégie"""
        try:
            # Essayer d'abord les stratégies hardcodées
            strategy_mapping = {
                "MovingAverage": ("strategies.moving_average", "MovingAverageStrategy"),
                "RSI": ("strategies.rsi_strategy", "RSIStrategy"),
                "MACrossoverAdvanced": (
                    "strategies.advanced_strategies",
                    "MACrossoverAdvanced",
                ),
                "MeanReversion": (
                    "strategies.advanced_strategies",
                    "MeanReversionStrategy",
                ),
                "Breakout": ("strategies.advanced_strategies", "BreakoutStrategy"),
            }

            if self.name in strategy_mapping:
                module_name, class_name = strategy_mapping[self.name]
                module = importlib.import_module(module_name)
                return getattr(module, class_name)

            # Sinon, essayer de charger dynamiquement
            # Format attendu: strategies.nom_strategie.NomStrategie
            module_name = f"strategies.{self.name.lower()}"
            module = importlib.import_module(module_name)

            # Chercher la classe
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, bt.Strategy)
                    and attr != bt.Strategy
                ):
                    return attr

            raise ValueError(f"Aucune classe de stratégie trouvée dans {module_name}")

        except Exception as e:
            logger.error(f"Erreur chargement stratégie {self.name}: {e}")
            raise

    def start(self):
        """Démarre la stratégie dans un thread séparé"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"Stratégie {self.name} démarrée")

    def _run(self):
        """Exécute la stratégie"""
        try:
            # Vérifier le circuit breaker avant de démarrer
            if self.circuit_breaker and not self.circuit_breaker.check_conditions(
                self.cerebro.broker.getvalue()
            ):
                logger.warning(f"Stratégie {self.name} bloquée par circuit breaker")
                return

            # Lancer Cerebro
            self.results = self.cerebro.run()

            # Mettre à jour les performances
            self._update_performance()

        except Exception as e:
            logger.error(f"Erreur exécution stratégie {self.name}: {e}")
        finally:
            self.running = False

    def stop(self):
        """Arrête la stratégie"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info(f"Stratégie {self.name} arrêtée")

    def _update_performance(self):
        """Met à jour les métriques de performance"""
        try:
            if self.results and len(self.results) > 0:
                strat = self.results[0]

                # Récupérer les analyseurs
                if hasattr(strat, "analyzers"):
                    # Sharpe Ratio
                    if hasattr(strat.analyzers, "sharpe"):
                        sharpe = strat.analyzers.sharpe.get_analysis()
                        self.performance["sharpe"] = sharpe.get("sharperatio", 0)

                    # Drawdown
                    if hasattr(strat.analyzers, "drawdown"):
                        dd = strat.analyzers.drawdown.get_analysis()
                        self.performance["drawdown"] = dd.get("drawdown", 0)

                    # Trades
                    if hasattr(strat.analyzers, "trades"):
                        trades = strat.analyzers.trades.get_analysis()
                        total = trades.get("total", {})
                        self.performance["trades"] = total.get("total", 0)

                        won = trades.get("won", {}).get("total", 0)
                        if self.performance["trades"] > 0:
                            self.performance["win_rate"] = (
                                won / self.performance["trades"]
                            )

                # PnL
                final_value = self.cerebro.broker.getvalue()
                initial_value = self.config["capital_allocation"]
                self.performance["pnl"] = final_value - initial_value

                self.performance["last_update"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Erreur mise à jour performance {self.name}: {e}")


class MultiStrategyRunner:
    """
    Orchestrateur pour gérer plusieurs stratégies en parallèle
    """

    def __init__(self, config, store, circuit_breaker=None, portfolio_manager=None):
        """
        Initialise le runner multi-stratégies

        Args:
            config: Configuration du paper trading
            store: AlpacaStore instance
            circuit_breaker: Circuit breaker (optionnel)
            portfolio_manager: Portfolio state manager (optionnel)
        """
        self.config = config
        self.store = store
        self.circuit_breaker = circuit_breaker
        self.portfolio_manager = portfolio_manager

        # Stratégies
        self.strategies = {}
        self.executor = ThreadPoolExecutor(max_workers=5)

        # État global
        self.running = False
        self._lock = threading.Lock()

        logger.info("MultiStrategyRunner initialisé")

    def initialize(self):
        """Initialise toutes les stratégies"""
        try:
            for strat_config in self.config["strategies"]:
                if not strat_config.get("enabled", True):
                    logger.info(f"Stratégie {strat_config['name']} désactivée")
                    continue

                # Créer l'instance
                strategy = StrategyInstance(
                    name=strat_config["name"],
                    config=strat_config,
                    store=self.store,
                    circuit_breaker=self.circuit_breaker,
                )

                # Initialiser
                strategy.initialize()

                # Ajouter à la liste
                self.strategies[strat_config["name"]] = strategy

            logger.info(f"{len(self.strategies)} stratégies initialisées")

        except Exception as e:
            logger.error(f"Erreur initialisation multi-stratégies: {e}")
            raise

    def start(self):
        """Démarre toutes les stratégies"""
        if not self.running:
            self.running = True

            # Démarrer chaque stratégie
            for name, strategy in self.strategies.items():
                self.executor.submit(strategy.start)
                logger.info(f"Stratégie {name} soumise pour exécution")

            logger.info("Toutes les stratégies démarrées")

    def stop(self):
        """Arrête toutes les stratégies"""
        self.running = False

        # Arrêter chaque stratégie
        for name, strategy in self.strategies.items():
            strategy.stop()

        # Arrêter l'executor
        self.executor.shutdown(wait=True, timeout=10)

        logger.info("Toutes les stratégies arrêtées")

    def get_performance(self):
        """Retourne les performances de toutes les stratégies"""
        performance = {"total_pnl": 0, "total_trades": 0, "strategies": {}}

        with self._lock:
            for name, strategy in self.strategies.items():
                perf = strategy.performance.copy()
                performance["strategies"][name] = perf
                performance["total_pnl"] += perf["pnl"]
                performance["total_trades"] += perf["trades"]

        performance["timestamp"] = datetime.now().isoformat()
        return performance

    def get_status(self):
        """Retourne le statut de toutes les stratégies"""
        status = {"running": self.running, "strategies": {}}

        for name, strategy in self.strategies.items():
            status["strategies"][name] = {
                "enabled": True,
                "running": strategy.running,
                "symbols": strategy.config["symbols"],
                "capital": strategy.config["capital_allocation"],
                "last_update": strategy.performance.get("last_update"),
            }

        return status

    def rebalance(self):
        """Rééquilibre le capital entre les stratégies"""
        # TODO: Implémenter la logique de rééquilibrage
        logger.info("Rééquilibrage des stratégies")

    def add_strategy(self, strat_config):
        """Ajoute une nouvelle stratégie à chaud"""
        try:
            if strat_config["name"] in self.strategies:
                logger.warning(f"Stratégie {strat_config['name']} déjà existante")
                return False

            # Créer et initialiser
            strategy = StrategyInstance(
                name=strat_config["name"],
                config=strat_config,
                store=self.store,
                circuit_breaker=self.circuit_breaker,
            )
            strategy.initialize()

            # Ajouter et démarrer si le runner tourne
            with self._lock:
                self.strategies[strat_config["name"]] = strategy
                if self.running:
                    self.executor.submit(strategy.start)

            logger.info(f"Stratégie {strat_config['name']} ajoutée")
            return True

        except Exception as e:
            logger.error(f"Erreur ajout stratégie: {e}")
            return False

    def remove_strategy(self, name):
        """Retire une stratégie"""
        with self._lock:
            if name in self.strategies:
                self.strategies[name].stop()
                del self.strategies[name]
                logger.info(f"Stratégie {name} retirée")
                return True
        return False
