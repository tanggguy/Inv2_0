# 🚀 Système de Trading Algorithmique

Système professionnel de trading algorithmique basé sur Backtrader avec architecture modulaire.

## 📋 Fonctionnalités

- ✅ Backtesting rigoureux sur données historiques
- ✅ Gestion des risques intégrée
- ✅ Support multi-stratégies
- ✅ Monitoring et alertes en temps réel
- ✅ Rapports de performance détaillés
- ✅ Support actions, crypto, forex

## 🛠️ Installation

### 1. Cloner et setup
```bash
cd trading_system
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 3. Installation TA-Lib (optionnel)
Voir: https://github.com/mrjbq7/ta-lib#installation

## 🚀 Utilisation

### Lancer un Backtest
```bash
python main.py --mode backtest --strategy MovingAverage --symbols AAPL,MSFT
```

### Mode Paper Trading
```bash
python main.py --mode paper --strategy RSI
```

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
├── run_dashboard.py  
└── dashboard/             # Interface Streamlit
    ├── app.py
    ├── pages/
    └── components/
```

```
scripts/
├── create_strategy.py        # Création interactive de stratégies
├── quick_start.py           # optimisation rapide 
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
└── strategy_templates.py    # Templates
```





## 📊 Exemple de Stratégie

Voir `strategies/moving_average.py` pour un exemple complet.

## 📝 Documentation

Documentation complète dans `/docs` (à venir)

Fonctionnalités Futures
En développement

 Paper trading en temps réel
 Dashboard web interactif
 Optimisation automatique des paramètres
 Backtesting walk-forward
 Intégration avec plusieurs courtiers
 Alertes Telegram/Email
 Machine Learning integration
 Portfolio optimization


