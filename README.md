# 🚀 Système de Trading Algorithmique

Système professionnel de trading algorithmique basé sur Backtrader avec architecture modulaire.

## 📋 Fonctionnalités

- Backtesting 
- Optimisation (optuna)
- Paper trading (alpaca)

## 🛠️ Installation

### 1. Setup
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```


## Utilisation

/scripts

/doc/CLI

## 📁 Structure
```
inv2_0/
├── backtesting/     # Moteur backtest
├── config/          # Configuration optimization_presets.json
├── data/            # Gestion données
├── monitoring/      # Logs & alertes
├── optimisation/    # 
├── paper_trading/    # 
├── risk_management/ # Gestion risques
├── scripts/         # create_strategy quick_start.py 
├── strategies/      # Stratégies de trading
├── execution/       # Exécution ordres
└── utils/           # Utilitaires
└──main
```

```
backtesting/
├── backtest_engine.py     # Moteur principal
├── performance_analyzer.py # Analyse performances
└── position_sizer.py      # Gestion positions
```

```
config/
├── optimization_presets.json     
├── settings.py
├── paper_trading_config.py
└── strategies_config.yaml     
```

```
data/
├── data_handler.py        # Gestion données
├── data_fetcher.py       # Téléchargement
```

```
monitoring/
├── logger.py             # Logging centralisé
```

```
paper_trading/             
├── __init__.py
├── paper_engine.py         # Moteur principal paper trading
├── alpaca_store.py         # Store Backtrader pour Alpaca
├── alpaca_broker.py        # Broker Backtrader pour Alpaca
├── alpaca_data.py          # DataFeed temps réel Alpaca
├── portfolio_state.py      # Sauvegarde état portefeuille
├── circuit_breaker.py      # Circuit breakers & risk controls
└── multi_strategy_runner.py # Orchestrateur multi-stratégies
```

```
optimization/
├── optimizer.py            # Moteur d'optimisation
├── optimizer_worker.py
├── results_storage.py      # Stockage résultats
├── optimization_config.py  # Configuration
├── optuna_optimizer.py  
├── optuna_presets.py
└── dashboard/             # Interface Streamlit
    ├── app.py
    ├── pages/
    └── components/
```

```
scripts/
├── create_strategy.py        # Création interactive de stratégies
├── quick_start.py           # optimisation rapide run_dashboard.py
├── run_dashboard.py
└── start_paper_trading.py   # Démarrage du paper trading
```

```
strategies/
├── base_strategy.py           # Classe de base
├── moving_average.py         # Stratégie MA
├── rsi_strategy.py          # Stratégie RSI
├── advanced_strategies.py   # Stratégies avancées
├── masuperstrategie.py
├── strategy_builder.py
├── squeezemomentum.md
└── strategy_templates.py    # Templates
```

## 📁 Structure complete

inv2_0/
├── backtesting/          # Moteur de backtest et analyse de performance
│   ├── __init__.py
│   ├── backtest_engine.py
│   └── performance_analyzer.py
│
├── config/               # Fichiers de configuration
│   ├── optimization_presets.json
│   ├── paper_trading_config.py
│   ├── settings.py
│   └── strategies_config.yaml
│
├── data/                 # Gestion et récupération des données de marché
│   ├── data_fetcher.py
│   └── data_handler.py
│
├── monitoring/           # Journalisation (logs) et notifications
│   ├── logger.py
│   └── telegram_notifier.py
│
├── optimization/         # Moteur d'optimisation et dashboard
│   ├── __init__.py
│   ├── optimization_config.py
│   ├── optimizer.py
│   ├── optimizer_worker.py
│   ├── optuna_optimizer.py
│   ├── optuna_presets.py
│   ├── results_storage.py
│   └── dashboard/
│       ├── app.py
│       ├── strategy_adapter.py
│       ├── components/charts.py, metrics.py, ...
│       └── pages/1_Run_Optimization.py, 2_View_History.py, ...
│
├── paper_trading/        # Moteur de trading simulé (paper trading)
│   ├── __init__.py
│   ├── alpaca_broker.py
│   ├── alpaca_data.py
│   ├── alpaca_store.py
│   ├── circuit_breaker.py
│   ├── multi_strategy_runner.py
│   ├── paper_engine.py
│   └── portfolio_state.py
│
├── risk_management/      # Gestion du risque et dimensionnement des positions
│   ├── position_sizer.py
│   └── risk_manager.py
│
├── scripts/              # Scripts utilitaires pour automatiser les tâches
│   ├── create_strategy.py
│   ├── optimize_my_strategy.py
│   ├── optimize_strategy.py
│   ├── optimize_with_viz.py
│   ├── quick_optimize.py
│   ├── run_dashboard.py
│   ├── start_paper_trading.py
│   └── walk_forward_optimization.py
│
├── strategies/           # Logique des stratégies de trading
│   ├── advanced_strategies.py
│   ├── base_strategy.py
│   ├── bollingerbands.py
│   ├── masuperstrategie.py
│   ├── moving_average.py
│   ├── rsi_strategy.py
│   ├── squeezemomentumstrategy.py
│   ├── strategy_builder.py
│   └── strategy_templates.py
│
├── tests/                # Tests unitaires et d'intégration
│   ├── check_installation_paper_trading.py
│   ├── test_config_adaptation.py
│   ├── test_newoptimizer.py
│   ├── test_optuna.py
│   ├── test_paper_trading.py
│   ├── test_parallel.py
│   ├── ... (et autres fichiers de test)
│
├── utils/                # Fonctions et classes utilitaires
│   ├── helpers.py
│   ├── indicators.py
│   └── validators.py
│
├── .env.example          # Fichier d'exemple pour les variables d'environnement
├── fix.py                # Script de correction (à usage spécifique)
└── main.py               # Point d'entrée principal de l'application


## 📝 Documentation

Documentation complète dans `/docs` 




