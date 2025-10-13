"""
Presets de configuration pour Optuna

À ajouter dans optimization/presets/ ou intégrer dans optimization_config.py
"""

OPTUNA_PRESETS = {
    'optuna_quick': {
        'description': 'Optimisation Optuna rapide (50 trials)',
        'symbol': 'AAPL',
        'timeframe': '1H',
        'period': {
            'start': '2023-01-01',
            'end': '2024-01-01'
        },
        'cash': 100000,
        'commission': 0.001,
        'param_grid': {
            'period': [10, 15, 20, 25, 30, 35, 40, 45, 50],
            'multiplier': [1.0, 1.5, 2.0, 2.5, 3.0],
            'risk_pct': [0.01, 0.015, 0.02, 0.025, 0.03]
        },
        'optuna': {
            'n_trials': 50,
            'timeout': None,
            'sampler': 'tpe',  # 'tpe', 'random'
            'pruner': 'median',  # 'median', 'successive_halving', 'none'
            'save_plots': True
        },
        'optimize_metric': 'sharpe',  # Métrique à maximiser
        'early_stopping': {
            'enabled': False  # Pas nécessaire avec Optuna
        }
    },
    
    'optuna_standard': {
        'description': 'Optimisation Optuna standard (100 trials)',
        'symbol': 'AAPL',
        'timeframe': '1H',
        'period': {
            'start': '2018-01-01',
            'end': '2024-01-01'
        },
        'cash': 100000,
        'commission': 0.001,
        'param_grid': {
            'period': list(range(10, 51, 2)),  # 10 à 50 par pas de 2
            'multiplier': [i/10 for i in range(10, 36, 2)],  # 1.0 à 3.5
            'risk_pct': [i/1000 for i in range(5, 31, 2)]  # 0.005 à 0.03
        },
        'optuna': {
            'n_trials': 100,
            'timeout': 3600,  # 1 heure max
            'sampler': 'tpe',
            'pruner': 'median',
            'save_plots': True
        },
        'optimize_metric': 'sharpe'
    },
    
    'optuna_deep': {
        'description': 'Optimisation Optuna approfondie (200 trials)',
        'symbol': 'AAPL',
        'timeframe': '1H',
        'period': {
            'start': '2020-01-01',
            'end': '2024-01-01'
        },
        'cash': 100000,
        'commission': 0.001,
        'param_grid': {
            'period': list(range(5, 101, 1)),
            'multiplier': [i/10 for i in range(5, 51, 1)],
            'risk_pct': [i/1000 for i in range(5, 51, 1)]
        },
        'optuna': {
            'n_trials': 200,
            'timeout': 7200,  # 2 heures max
            'sampler': 'tpe',
            'pruner': 'median',
            'save_plots': True
        },
        'optimize_metric': 'sharpe'
    },
    
    'optuna_ultra': {
        'description': 'Optimisation Optuna ultra (500 trials - nuit)',
        'symbol': 'AAPL',
        'timeframe': '1D',
        'period': {
            'start': '2018-01-01',
            'end': '2024-01-01'
        },
        'cash': 100000,
        'commission': 0.001,
        'param_grid': {
            'period': list(range(5, 201, 1)),
            'multiplier': [i/10 for i in range(5, 101, 1)],
            'risk_pct': [i/1000 for i in range(5, 101, 1)],
            'stop_loss': [i/100 for i in range(1, 21, 1)]
        },
        'optuna': {
            'n_trials': 500,
            'timeout': None,  # Pas de limite
            'sampler': 'tpe',
            'pruner': 'successive_halving',  # Plus agressif
            'save_plots': True
        },
        'optimize_metric': 'sharpe'
    },
    
    'optuna_multiobj': {
        'description': 'Optimisation multi-objectif (Sharpe + Return + Drawdown)',
        'symbol': 'AAPL',
        'timeframe': '1H',
        'period': {
            'start': '2022-01-01',
            'end': '2024-01-01'
        },
        'cash': 100000,
        'commission': 0.001,
        'param_grid': {
            'period': list(range(10, 51, 2)),
            'multiplier': [i/10 for i in range(10, 36, 2)],
            'risk_pct': [i/1000 for i in range(5, 31, 2)]
        },
        'optuna': {
            'n_trials': 150,
            'timeout': None,
            'sampler': 'tpe',
            'pruner': 'median',
            'save_plots': True,
            'multi_objective': True,  # Active le mode multi-objectif
            'objectives': ['sharpe', 'return', 'drawdown']  # Objectifs à optimiser
        },
        'optimize_metric': 'sharpe'  # Métrique principale
    }
}


def get_optuna_preset(preset_name: str) -> dict:
    """Retourne un preset Optuna"""
    if preset_name not in OPTUNA_PRESETS:
        raise ValueError(f"Preset Optuna inconnu: {preset_name}")
    return OPTUNA_PRESETS[preset_name].copy()


def list_optuna_presets() -> list:
    """Liste tous les presets Optuna disponibles"""
    return list(OPTUNA_PRESETS.keys())