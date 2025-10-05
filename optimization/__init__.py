"""
Module d'optimisation pour le système de trading

Fonctionnalités:
- OptimizationConfig: Gestion des presets et configurations
- UnifiedOptimizer: Optimiseur unifié (Grid Search, Walk-Forward)
- ResultsStorage: Stockage et historique des résultats
- Support Grid Search, Walk-Forward, Random Search
"""

from optimization.optimization_config import OptimizationConfig, load_preset, get_strategy_params
from optimization.results_storage import ResultsStorage

__version__ = "1.0.0"
__all__ = ['OptimizationConfig', 'ResultsStorage', 'load_preset', 'get_strategy_params']
