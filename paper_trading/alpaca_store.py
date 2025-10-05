"""
Alpaca Store - Gestion de la connexion à l'API Alpaca
"""
import backtrader as bt
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
import asyncio
import threading
import queue
from datetime import datetime, timedelta
import pytz
from monitoring.logger import setup_logger

logger = setup_logger("alpaca_store")


class MetaSingleton(MetaParams):
    """Métaclasse Singleton pour le store"""
    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._singleton


class AlpacaStore(with_metaclass(MetaSingleton, object)):
    """
    Store principal pour Alpaca
    Gère la connexion API et les WebSockets
    """
    
    params = (
        ('api_key', None),
        ('secret_key', None),
        ('base_url', 'https://paper-api.alpaca.markets'),
        ('data_url', 'https://data.alpaca.markets'),
        ('data_feed', 'iex'),  # 'iex' ou 'sip'
        ('retry_attempts', 3),
        ('timeout', 30),
    )
    
    BrokerCls = None  # Sera défini dans alpaca_broker.py
    DataCls = None    # Sera défini dans alpaca_data.py
    
    def __init__(self, **kwargs):
        super(AlpacaStore, self).__init__()
        
        # Mise à jour des paramètres
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
        
        # Initialiser l'API Alpaca
        self._init_api()
        
        # WebSocket et threading
        self._websocket_thread = None
        self._ws_stop_event = threading.Event()
        self._data_queue = queue.Queue()
        self._subscriptions = {}
        
        # Cache des données
        self._bars_cache = {}
        self._positions_cache = {}
        self._account_cache = None
        self._last_cache_update = None
        
        logger.info(f"AlpacaStore initialisé avec {self.params.base_url}")
    
    def _init_api(self):
        """Initialise la connexion API Alpaca"""
        try:
            self.api = tradeapi.REST(
                key_id=self.params.api_key,
                secret_key=self.params.secret_key,
                base_url=self.params.base_url,
                api_version='v2'
            )
            
            # Vérifier la connexion
            account = self.api.get_account()
            logger.info(f"Connecté à Alpaca - Cash: ${account.cash}, Buying Power: ${account.buying_power}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à Alpaca: {e}")
            raise
    
    def start(self, data=None):
        """Démarre le store et les connexions WebSocket"""
        if not self._websocket_thread or not self._websocket_thread.is_alive():
            self._ws_stop_event.clear()
            self._websocket_thread = threading.Thread(target=self._run_websocket)
            self._websocket_thread.daemon = True
            self._websocket_thread.start()
            logger.info("WebSocket thread démarré")
    
    def stop(self):
        """Arrête les connexions et threads"""
        if self._websocket_thread and self._websocket_thread.is_alive():
            self._ws_stop_event.set()
            self._websocket_thread.join(timeout=5)
            logger.info("WebSocket thread arrêté")
    
    def _run_websocket(self):
        """Thread principal pour le WebSocket"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            logger.error(f"Erreur WebSocket: {e}")
        finally:
            loop.close()
    
    async def _websocket_handler(self):
        """Gestionnaire asynchrone du WebSocket"""
        from alpaca_trade_api.stream import Stream
        
        stream = Stream(
            self.params.api_key,
            self.params.secret_key,
            base_url=self.params.base_url,
            data_feed=self.params.data_feed
        )
        
        @stream.on_bar
        async def on_bar(bar):
            """Callback pour les barres reçues"""
            self._handle_bar(bar)
        
        @stream.on_trade_update
        async def on_trade_update(trade):
            """Callback pour les mises à jour de trades"""
            self._handle_trade_update(trade)
        
        # S'abonner aux symboles
        for symbol in self._subscriptions.keys():
            stream.subscribe_bars(on_bar, symbol)
            logger.info(f"Souscrit aux barres pour {symbol}")
        
        # Lancer le stream
        await stream._run_forever()
    
    def _handle_bar(self, bar):
        """Traite une barre reçue du WebSocket"""
        try:
            # Convertir en format Backtrader
            bar_data = {
                'datetime': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume),
            }
            
            # Mettre en cache
            if bar.symbol not in self._bars_cache:
                self._bars_cache[bar.symbol] = []
            self._bars_cache[bar.symbol].append(bar_data)
            
            # Limiter la taille du cache
            if len(self._bars_cache[bar.symbol]) > 200:
                self._bars_cache[bar.symbol].pop(0)
            
            # Envoyer aux données souscrites
            if bar.symbol in self._subscriptions:
                for data_feed in self._subscriptions[bar.symbol]:
                    data_feed._add_bar(bar_data)
            
        except Exception as e:
            logger.error(f"Erreur traitement barre: {e}")
    
    def _handle_trade_update(self, trade):
        """Traite une mise à jour de trade"""
        logger.info(f"Trade update: {trade.event} pour {trade.order.symbol} - Status: {trade.order.status}")
        # Le broker gérera les mises à jour de trades
        if hasattr(self, 'broker') and self.broker:
            self.broker._handle_trade_update(trade)
    
    def subscribe_bars(self, data_feed, symbol):
        """S'abonne aux barres pour un symbole"""
        if symbol not in self._subscriptions:
            self._subscriptions[symbol] = []
        self._subscriptions[symbol].append(data_feed)
        logger.info(f"Data feed souscrit pour {symbol}")
    
    def unsubscribe_bars(self, data_feed, symbol):
        """Se désabonne des barres pour un symbole"""
        if symbol in self._subscriptions:
            if data_feed in self._subscriptions[symbol]:
                self._subscriptions[symbol].remove(data_feed)
                if not self._subscriptions[symbol]:
                    del self._subscriptions[symbol]
    
    def get_positions(self):
        """Récupère les positions actuelles"""
        try:
            positions = self.api.list_positions()
            self._positions_cache = {p.symbol: p for p in positions}
            return self._positions_cache
        except Exception as e:
            logger.error(f"Erreur récupération positions: {e}")
            return self._positions_cache or {}
    
    def get_account(self):
        """Récupère les informations du compte"""
        try:
            self._account_cache = self.api.get_account()
            self._last_cache_update = datetime.now()
            return self._account_cache
        except Exception as e:
            logger.error(f"Erreur récupération compte: {e}")
            return self._account_cache
    
    def get_bars(self, symbol, timeframe='1H', limit=100):
        """Récupère les barres historiques"""
        try:
            # Convertir le timeframe
            tf = TimeFrame(1, TimeFrameUnit.Hour) if timeframe == '1H' else TimeFrame.Day
            
            # Calculer les dates
            end_date = datetime.now(pytz.timezone('US/Eastern'))
            start_date = end_date - timedelta(days=30)
            
            # Récupérer les barres
            bars_response = self.api.get_bars(
                symbol,
                tf,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                limit=limit,
                feed=self.params.data_feed
            )
            
            bars = []
            for bar in bars_response:
                bars.append({
                    'datetime': bar.t,
                    'open': float(bar.o),
                    'high': float(bar.h),
                    'low': float(bar.l),
                    'close': float(bar.c),
                    'volume': float(bar.v),
                })
            
            return bars
            
        except Exception as e:
            logger.error(f"Erreur récupération barres pour {symbol}: {e}")
            return []
    
    def submit_order(self, symbol, qty, side, order_type='market', 
                    limit_price=None, stop_price=None, time_in_force='day'):
        """Soumet un ordre à Alpaca"""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
            logger.info(f"Ordre soumis: {side} {qty} {symbol} @ {order_type}")
            return order
        except Exception as e:
            logger.error(f"Erreur soumission ordre: {e}")
            raise
    
    def cancel_order(self, order_id):
        """Annule un ordre"""
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Ordre {order_id} annulé")
            return True
        except Exception as e:
            logger.error(f"Erreur annulation ordre {order_id}: {e}")
            return False
    
    def get_order(self, order_id):
        """Récupère un ordre spécifique"""
        try:
            return self.api.get_order(order_id)
        except Exception as e:
            logger.error(f"Erreur récupération ordre {order_id}: {e}")
            return None
    
    def get_broker(self):
        """Retourne une instance du broker Alpaca"""
        if self.BrokerCls:
            return self.BrokerCls(store=self)
        return None
    
    def get_data(self, **kwargs):
        """Retourne une instance de données Alpaca"""
        if self.DataCls:
            return self.DataCls(store=self, **kwargs)
        return None