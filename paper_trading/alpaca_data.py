"""
Alpaca Data - Flux de données temps réel depuis Alpaca
"""

import backtrader as bt
from backtrader.feed import DataBase
from backtrader.utils.py3 import with_metaclass
from datetime import datetime, timedelta
import pytz
import threading
import queue
from monitoring.logger import setup_logger

logger = setup_logger("alpaca_data")


class AlpacaData(DataBase):
    """
    Data feed pour Alpaca
    Gère les données temps réel et historiques
    """

    params = (
        ("symbol", ""),
        ("timeframe", bt.TimeFrame.Minutes),
        ("compression", 60),  # 60 minutes = 1 heure
        ("historical", True),
        ("backfill_days", 100),
        ("live", True),
        ("qcheck", 0.5),
        ("reconnect", True),
        ("reconnect_attempts", 5),
    )

    def __init__(self, store, **kwargs):
        super(AlpacaData, self).__init__(**kwargs)

        self.store = store
        self._name = self.params.symbol

        # Files pour les données
        self._data_queue = queue.Queue()
        self._lock = threading.Lock()

        # État
        self._connected = False
        self._last_bar_time = None
        self._historical_loaded = False

        logger.info(f"AlpacaData créé pour {self.params.symbol}")

    def start(self):
        """Démarre le flux de données"""
        super(AlpacaData, self).start()

        # Charger l'historique si demandé
        if self.params.historical and not self._historical_loaded:
            self._load_historical()

        # S'abonner aux données temps réel
        if self.params.live:
            self.store.subscribe_bars(self, self.params.symbol)
            self._connected = True

        logger.info(f"Data feed démarré pour {self.params.symbol}")

    def stop(self):
        """Arrête le flux de données"""
        super(AlpacaData, self).stop()

        if self._connected:
            self.store.unsubscribe_bars(self, self.params.symbol)
            self._connected = False

        logger.info(f"Data feed arrêté pour {self.params.symbol}")

    def _load_historical(self):
        """Charge les données historiques"""
        try:
            logger.info(f"Chargement historique pour {self.params.symbol}...")

            # Déterminer le timeframe
            timeframe = "1H" if self.params.compression == 60 else "1D"

            # Récupérer les barres
            bars = self.store.get_bars(
                symbol=self.params.symbol,
                timeframe=timeframe,
                limit=(
                    self.params.backfill_days * 24
                    if timeframe == "1H"
                    else self.params.backfill_days
                ),
            )

            if bars:
                # Ajouter les barres à la queue
                for bar in bars:
                    self._data_queue.put(bar)

                self._historical_loaded = True
                logger.info(
                    f"{len(bars)} barres historiques chargées pour {self.params.symbol}"
                )
            else:
                logger.warning(f"Aucune donnée historique pour {self.params.symbol}")

        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")

    def _add_bar(self, bar):
        """Ajoute une barre depuis le WebSocket"""
        try:
            with self._lock:
                self._data_queue.put(bar)
                logger.debug(
                    f"Barre ajoutée pour {self.params.symbol}: {bar['datetime']}"
                )
        except Exception as e:
            logger.error(f"Erreur ajout barre: {e}")

    def _load(self):
        """Charge la prochaine barre de données"""
        try:
            # Vérifier s'il y a des données dans la queue
            if not self._data_queue.empty():
                try:
                    bar = self._data_queue.get_nowait()

                    # Convertir le datetime si nécessaire
                    if isinstance(bar["datetime"], str):
                        dt = datetime.fromisoformat(
                            bar["datetime"].replace("Z", "+00:00")
                        )
                    else:
                        dt = bar["datetime"]

                    # Convertir en timezone Eastern
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    dt = dt.astimezone(pytz.timezone("US/Eastern"))

                    # Mettre à jour les lignes de données
                    self.lines.datetime[0] = bt.date2num(dt)
                    self.lines.open[0] = bar["open"]
                    self.lines.high[0] = bar["high"]
                    self.lines.low[0] = bar["low"]
                    self.lines.close[0] = bar["close"]
                    self.lines.volume[0] = bar["volume"]
                    self.lines.openinterest[0] = 0

                    self._last_bar_time = dt

                    return True

                except queue.Empty:
                    pass

            # Si on est en mode live et qu'il n'y a pas de données
            if self.params.live and self._connected:
                # Retourner None pour attendre de nouvelles données
                return None

            # Sinon, fin des données
            return False

        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            return False

    def islive(self):
        """Indique si le flux est en temps réel"""
        return self.params.live and self._connected

    def haslivedata(self):
        """Indique si des données temps réel sont disponibles"""
        return self._connected and not self._data_queue.empty()


class AlpacaDataFactory:
    """Factory pour créer des data feeds Alpaca"""

    @staticmethod
    def create_data(store, symbol, timeframe="1H", historical=True, backfill_days=100):
        """
        Crée un data feed Alpaca

        Args:
            store: AlpacaStore instance
            symbol: Symbole à trader
            timeframe: Timeframe ('1H', '1D', etc.)
            historical: Charger l'historique
            backfill_days: Nombre de jours d'historique
        """
        # Déterminer le timeframe et compression
        if timeframe == "1H":
            tf = bt.TimeFrame.Minutes
            compression = 60
        elif timeframe == "15M":
            tf = bt.TimeFrame.Minutes
            compression = 15
        elif timeframe == "5M":
            tf = bt.TimeFrame.Minutes
            compression = 5
        elif timeframe == "1D":
            tf = bt.TimeFrame.Days
            compression = 1
        else:
            tf = bt.TimeFrame.Minutes
            compression = 60

        return AlpacaData(
            store=store,
            symbol=symbol,
            timeframe=tf,
            compression=compression,
            historical=historical,
            backfill_days=backfill_days,
            live=True,
        )


# Enregistrer le data dans le store
from . import alpaca_store

alpaca_store.AlpacaStore.DataCls = AlpacaData
