"""
Alpaca Broker - Gestion des ordres et positions avec Alpaca
"""
import backtrader as bt
from backtrader.broker import BrokerBase
from backtrader.order import Order, OrderBase
from backtrader.position import Position
from datetime import datetime
import threading
from monitoring.logger import setup_logger

logger = setup_logger("alpaca_broker")


class AlpacaOrder(OrderBase):
    """Ordre spécifique pour Alpaca"""
    
    def __init__(self, owner, data, alpaca_order=None):
        super(AlpacaOrder, self).__init__()
        self.owner = owner
        self.data = data
        self.alpaca_order = alpaca_order
        self.executed_fills = []


class AlpacaBroker(BrokerBase):
    """
    Broker pour Alpaca
    Gère l'exécution des ordres et le suivi des positions
    """
    
    params = (
        ('use_positions', True),
        ('commission', 0.0),  # Alpaca n'a pas de commissions
        ('fill_delay', 0.1),
        ('slip_perc', 0.0),
        ('slip_fixed', 0.0),
        ('slip_open', False),
        ('slip_match', True),
        ('slip_limit', True),
        ('slip_out', False),
    )
    
    def __init__(self, store, **kwargs):
        super(AlpacaBroker, self).__init__()
        self.store = store
        
        # État du broker
        self._cash = 0.0
        self._value = 0.0
        self._orders = {}  # order_id -> AlpacaOrder
        self._positions = {}  # symbol -> position
        
        # Threading
        self._lock = threading.Lock()
        
        # Synchroniser avec Alpaca
        self._sync_account()
        
        # Enregistrer le broker dans le store
        store.broker = self
        
        logger.info("AlpacaBroker initialisé")
    
    def _sync_account(self):
        """Synchronise l'état du compte avec Alpaca"""
        try:
            account = self.store.get_account()
            if account:
                self._cash = float(account.cash)
                self._value = float(account.portfolio_value)
                logger.info(f"Compte synchronisé - Cash: ${self._cash:.2f}, Value: ${self._value:.2f}")
            
            # Synchroniser les positions
            positions = self.store.get_positions()
            for symbol, position in positions.items():
                self._positions[symbol] = {
                    'size': int(position.qty),
                    'price': float(position.avg_entry_price),
                    'value': float(position.market_value),
                    'pnl': float(position.unrealized_pl)
                }
                logger.info(f"Position {symbol}: {position.qty} @ ${position.avg_entry_price}")
                
        except Exception as e:
            logger.error(f"Erreur synchronisation compte: {e}")
    
    def start(self):
        """Démarre le broker"""
        super(AlpacaBroker, self).start()
        self.store.start()
        logger.info("Broker démarré")
    
    def stop(self):
        """Arrête le broker"""
        super(AlpacaBroker, self).stop()
        logger.info("Broker arrêté")
    
    def getcash(self):
        """Retourne le cash disponible"""
        return self._cash
    
    def getvalue(self, datas=None):
        """Retourne la valeur totale du portefeuille"""
        return self._value
    
    def getposition(self, data, clone=True):
        """Retourne la position pour un data"""
        symbol = data._name if hasattr(data, '_name') else str(data)
        
        if symbol in self._positions:
            pos = self._positions[symbol]
            position = Position()
            position.size = pos['size']
            position.price = pos['price']
            return position
        
        # Retourner une position vide
        return Position()
    
    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            **kwargs):
        """Créer un ordre d'achat"""
        return self._submit_order(owner, data, size, 'buy', price, exectype, **kwargs)
    
    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             **kwargs):
        """Créer un ordre de vente"""
        return self._submit_order(owner, data, size, 'sell', price, exectype, **kwargs)
    
    def _submit_order(self, owner, data, size, side, price=None, exectype=None, **kwargs):
        """Soumet un ordre à Alpaca"""
        try:
            symbol = data._name if hasattr(data, '_name') else str(data)
            
            # Déterminer le type d'ordre
            order_type = 'market'
            limit_price = None
            stop_price = None
            
            if exectype == Order.Limit:
                order_type = 'limit'
                limit_price = price
            elif exectype == Order.Stop:
                order_type = 'stop'
                stop_price = price
            elif exectype == Order.StopLimit:
                order_type = 'stop_limit'
                stop_price = price
                limit_price = kwargs.get('plimit', price)
            
            # Créer l'ordre Backtrader
            order = AlpacaOrder(owner, data)
            order.created.size = size
            order.created.price = price or 0
            order.data = data
            order.size = size
            order.price = price
            order.exectype = exectype or Order.Market
            order.status = Order.Submitted
            
            # Soumettre à Alpaca
            alpaca_side = 'buy' if side == 'buy' else 'sell'
            alpaca_order = self.store.submit_order(
                symbol=symbol,
                qty=abs(int(size)),
                side=alpaca_side,
                order_type=order_type,
                limit_price=limit_price,
                stop_price=stop_price,
                time_in_force='day'
            )
            
            if alpaca_order:
                order.alpaca_order = alpaca_order
                order.ref = alpaca_order.id
                
                with self._lock:
                    self._orders[alpaca_order.id] = order
                
                # Notifier la stratégie
                self.notify(order)
                logger.info(f"Ordre soumis: {alpaca_side} {size} {symbol} @ {order_type}")
                
                return order
            else:
                order.status = Order.Rejected
                self.notify(order)
                return order
                
        except Exception as e:
            logger.error(f"Erreur soumission ordre: {e}")
            order = AlpacaOrder(owner, data)
            order.status = Order.Rejected
            self.notify(order)
            return order
    
    def cancel(self, order):
        """Annule un ordre"""
        try:
            if hasattr(order, 'alpaca_order') and order.alpaca_order:
                success = self.store.cancel_order(order.alpaca_order.id)
                if success:
                    order.status = Order.Canceled
                    self.notify(order)
                    
                    with self._lock:
                        if order.ref in self._orders:
                            del self._orders[order.ref]
                    
                    logger.info(f"Ordre {order.ref} annulé")
                    return order
            
        except Exception as e:
            logger.error(f"Erreur annulation ordre: {e}")
        
        return order
    
    def notify(self, order):
        """Notifie la stratégie d'un changement d'ordre"""
        if hasattr(order.owner, '_notify'):
            order.owner._notify(order)
    
    def _handle_trade_update(self, trade):
        """Gère les mises à jour de trades d'Alpaca"""
        try:
            order_id = trade.order.id
            
            with self._lock:
                if order_id not in self._orders:
                    return
                
                order = self._orders[order_id]
                
                # Mettre à jour le statut
                if trade.event == 'fill' or trade.event == 'partial_fill':
                    # Ordre exécuté
                    order.status = Order.Completed if trade.event == 'fill' else Order.Partial
                    order.executed.size = float(trade.order.filled_qty)
                    order.executed.price = float(trade.order.filled_avg_price) if trade.order.filled_avg_price else 0
                    order.executed.value = order.executed.size * order.executed.price
                    order.executed.comm = 0  # Pas de commission chez Alpaca
                    order.executed.dt = bt.date2num(datetime.now())
                    
                    # Mettre à jour les positions internes
                    symbol = trade.order.symbol
                    if symbol not in self._positions:
                        self._positions[symbol] = {
                            'size': 0,
                            'price': 0,
                            'value': 0,
                            'pnl': 0
                        }
                    
                    if trade.order.side == 'buy':
                        self._positions[symbol]['size'] += float(trade.order.filled_qty)
                    else:
                        self._positions[symbol]['size'] -= float(trade.order.filled_qty)
                    
                    # Mise à jour du cash
                    if trade.order.side == 'buy':
                        self._cash -= order.executed.value
                    else:
                        self._cash += order.executed.value
                    
                    logger.info(f"Trade exécuté: {trade.order.side} {trade.order.filled_qty} {symbol} @ ${trade.order.filled_avg_price}")
                    
                elif trade.event == 'rejected' or trade.event == 'canceled':
                    # Ordre rejeté ou annulé
                    order.status = Order.Rejected if trade.event == 'rejected' else Order.Canceled
                    logger.info(f"Ordre {order_id} {trade.event}")
                
                # Notifier la stratégie
                self.notify(order)
                
                # Supprimer l'ordre s'il est terminé
                if order.status in [Order.Completed, Order.Canceled, Order.Rejected]:
                    if order_id in self._orders:
                        del self._orders[order_id]
                    
        except Exception as e:
            logger.error(f"Erreur traitement trade update: {e}")
    
    def next(self):
        """Appelé à chaque itération"""
        # Synchroniser périodiquement avec Alpaca
        pass
    
    def get_notification(self):
        """Récupère les notifications (non utilisé avec Alpaca)"""
        return None
    
    def get_fundmode(self):
        """Retourne le mode de financement"""
        return False
    
    def get_fundshares(self):
        """Retourne les parts du fonds"""
        return 1.0


# Enregistrer le broker dans le store
from . import alpaca_store
alpaca_store.AlpacaStore.BrokerCls = AlpacaBroker