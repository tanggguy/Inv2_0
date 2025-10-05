"""
Module Paper Trading avec Alpaca

Système de trading temps réel en mode paper (simulation) avec Alpaca
"""

from .paper_engine import PaperTradingEngine
from .alpaca_store import AlpacaStore
from .alpaca_broker import AlpacaBroker
from .alpaca_data import AlpacaData
from .portfolio_state import PortfolioStateManager
from .circuit_breaker import CircuitBreaker
from .multi_strategy_runner import MultiStrategyRunner

__version__ = '1.0.0'
__author__ = 'Trading System'

__all__ = [
    'PaperTradingEngine',
    'AlpacaStore',
    'AlpacaBroker',
    'AlpacaData',
    'PortfolioStateManager',
    'CircuitBreaker',
    'MultiStrategyRunner',
]