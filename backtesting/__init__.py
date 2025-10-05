# __init__.py for the backtesting package

"""
Package backtesting - Moteur de backtest et analyse de performance

Composants:
- BacktestEngine: Moteur principal de backtesting
- PerformanceAnalyzer: Analyse des résultats et métriques

Usage:
    from backtesting import BacktestEngine, PerformanceAnalyzer
    
    engine = BacktestEngine(strategy='MovingAverage', symbols=['AAPL'])
    results = engine.run()
    
    analyzer = PerformanceAnalyzer(results)
    metrics = analyzer.get_metrics()
"""

from backtesting.backtest_engine import BacktestEngine
from backtesting.performance_analyzer import PerformanceAnalyzer

__version__ = "1.0.0"
__all__ = ['BacktestEngine', 'PerformanceAnalyzer']