# 📈 Module Paper Trading avec Alpaca

## Vue d'ensemble

Le module Paper Trading permet de tester vos stratégies en temps réel avec des données de marché en direct, sans risquer d'argent réel. Il utilise l'API Paper Trading d'Alpaca pour simuler des transactions réelles.

## 🚀 Démarrage Rapide

### 1. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env et ajouter vos clés API Alpaca
nano .env
```

**Clés requises:**
- `ALPACA_API_KEY`: Votre clé API Alpaca (paper trading)
- `ALPACA_SECRET_KEY`: Votre clé secrète Alpaca

**Obtenir les clés:** Créez un compte gratuit sur [Alpaca](https://alpaca.markets/) et récupérez vos clés API paper trading.

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer le Paper Trading

```bash
# Méthode simple
python start_paper_trading.py

# Ou via le script principal
python main.py --mode paper
```

## 📁 Structure du Module

```
paper_trading/
├── __init__.py              # Module principal
├── paper_engine.py          # Moteur principal de coordination
├── alpaca_store.py          # Connexion et gestion API Alpaca
├── alpaca_broker.py         # Exécution des ordres
├── alpaca_data.py           # Flux de données temps réel
├── portfolio_state.py       # Sauvegarde/restauration état
├── circuit_breaker.py       # Protection et gestion des risques
└── multi_strategy_runner.py # Orchestration multi-stratégies
```

## ⚙️ Configuration

### Configuration des Stratégies

Éditez `config/paper_trading_config.py`:

```python
"strategies": [
    {
        "name": "MovingAverage",
        "enabled": True,
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "capital_allocation": 50000,
        "params": {
            "ma_period": 20,
            "stop_loss_pct": 0.02,
        }
    },
    # Ajouter d'autres stratégies...
]
```

### Circuit Breakers

Protégez votre capital avec des limites automatiques:

```python
"circuit_breakers": {
    "max_drawdown_pct": 0.20,      # Pause si drawdown > 20%
    "max_daily_trades": 50,         # Max 50 trades/jour
    "max_consecutive_losses": 5,    # Pause après 5 pertes consécutives
    "max_daily_loss_pct": 0.05,     # Pause si perte jour > 5%
}
```

### Notifications Telegram (Optionnel)

1. Créez un bot Telegram avec [@BotFather](https://t.me/botfather)
2. Obtenez votre Chat ID avec [@userinfobot](https://t.me/userinfobot)
3. Configurez dans `.env`:

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📊 Fonctionnalités

### ✅ Implémentées

- **Trading Multi-Stratégies**: Exécutez plusieurs stratégies en parallèle
- **Données Temps Réel**: WebSocket pour barres 1H en temps réel
- **Circuit Breakers**: Protection automatique contre les pertes
- **Sauvegarde d'État**: Récupération après crash
- **Notifications**: Alertes Telegram pour trades et événements
- **Allocation de Capital**: Gestion séparée par stratégie
- **Monitoring**: Suivi des performances en temps réel

### 🔄 États du Système

1. **Initialisation**: Connexion à Alpaca, chargement des stratégies
2. **Trading Actif**: Réception données, génération signaux, exécution ordres
3. **Circuit Break**: Pause temporaire si conditions dangereuses
4. **Arrêt**: Sauvegarde état final, fermeture connexions

## 🎯 Stratégies Disponibles

### Stratégies Incluses

1. **MovingAverage**: Croisement de moyennes mobiles
2. **RSI**: Surachat/Survente avec RSI
3. **MACrossoverAdvanced**: MACD avec gestion des risques
4. **MeanReversion**: Retour à la moyenne (Bollinger Bands)
5. **Breakout**: Cassure de résistance/support

### Ajouter une Stratégie

1. Créez votre stratégie dans `strategies/ma_strategie.py`:

```python
from strategies.base_strategy import BaseStrategy
import backtrader as bt

class MaStrategie(BaseStrategy):
    params = (
        ('period', 20),
        ('stop_loss_pct', 0.02),
    )
    
    def __init__(self):
        super().__init__()
        self.indicator = bt.indicators.SMA(period=self.params.period)
    
    def next(self):
        if self.position:
            # Logique de vente
            if condition_vente:
                self.sell()
        else:
            # Logique d'achat
            if condition_achat:
                self.buy()
```

2. Ajoutez-la dans `config/paper_trading_config.py`

## 📈 Monitoring

### Dashboard en Temps Réel

Le système affiche périodiquement:
- Valeur du portefeuille
- P&L global et par stratégie
- Nombre de trades
- État des circuit breakers

### Logs

Les logs sont sauvegardés dans `logs/`:
- `paper_engine.log`: Log principal
- `alpaca_store.log`: Connexions API
- `circuit_breaker.log`: Événements de protection

### États Sauvegardés

Les états sont sauvegardés dans `data_cache/portfolio_states/`:
- Sauvegarde automatique toutes les 5 minutes
- Format: `portfolio_state_YYYYMMDD_HHMMSS.json`
- Dernier état: `latest_state.json`

## 🛠️ Commandes Utiles

```bash
# Vérifier l'environnement
python scripts\start_paper_trading.py --check-only

# Afficher la configuration
python start_paper_trading.py --config

# Tester Telegram
python start_paper_trading.py --test-telegram

# Restaurer depuis le dernier état
python start_paper_trading.py --restore

# Mode verbose
python start_paper_trading.py --verbose
```

## ⚠️ Gestion des Erreurs

### Erreurs Communes

1. **"API key not found"**
   - Vérifiez vos clés dans `.env`
   - Assurez-vous d'utiliser les clés Paper Trading

2. **"WebSocket disconnected"**
   - Reconnexion automatique après 5 secondes
   - Vérifiez votre connexion internet

3. **"Circuit breaker triggered"**
   - Trading suspendu temporairement
   - Vérifiez les conditions dans les logs
   - Override manuel possible si nécessaire

### Recovery après Crash

Le système sauvegarde automatiquement l'état. Pour récupérer:

```bash
# Restauration automatique
python start_paper_trading.py --restore

# Ou copie manuelle
cp data_cache/portfolio_states/latest_state.json backup_state.json
```

## 📊 Analyse des Performances

### Exporter l'Historique

```python
from paper_trading.portfolio_state import PortfolioStateManager

manager = PortfolioStateManager(config)
history = manager.export_history(
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now(),
    output_file="trading_history.json"
)
```

### Métriques Disponibles

- **P&L**: Total et par stratégie
- **Win Rate**: Pourcentage de trades gagnants
- **Sharpe Ratio**: Rendement ajusté au risque
- **Drawdown**: Perte maximale depuis un pic
- **Trades**: Nombre total et par jour

## 🔒 Sécurité

### Bonnes Pratiques

1. **Ne jamais commiter `.env`**: Ajouté au `.gitignore`
2. **Utiliser Paper Trading d'abord**: Testez avant le live
3. **Circuit Breakers actifs**: Ne les désactivez pas
4. **Limites de position**: Max 25% par position par défaut
5. **Monitoring régulier**: Vérifiez les notifications

### Limites du Paper Trading

- **Pas de slippage réel**: Les exécutions peuvent différer en live
- **Liquidité illimitée**: Toujours possible d'acheter/vendre
- **Pas d'impact sur le marché**: Vos ordres n'affectent pas les prix
- **Psychologie différente**: Pas de stress d'argent réel

## 🚀 Passage en Live Trading

**⚠️ ATTENTION**: Le trading live utilise de l'argent réel!

1. Testez au moins 1 mois en paper trading
2. Vérifiez les performances et ajustez les paramètres
3. Changez l'URL dans `.env`:
   ```bash
   ALPACA_BASE_URL=https://api.alpaca.markets  # LIVE - DANGER!
   ```
4. Réduisez les tailles de position
5. Augmentez les circuit breakers
6. Surveillez activement

## 📚 Ressources

- [Documentation Alpaca](https://docs.alpaca.markets/)
- [API Reference](https://docs.alpaca.markets/reference/)
- [Backtrader Docs](https://www.backtrader.com/docu/)
- [Support Discord](https://discord.gg/alpaca)

## 🤝 Support

Pour toute question ou problème:
1. Consultez les logs dans `logs/`
2. Vérifiez la configuration dans `config/`
3. Testez avec `--check-only`
4. Activez le mode `--verbose`

## 📄 License

Ce module fait partie du système de trading algorithmique.
Utilisez à vos propres risques. Aucune garantie de profit.