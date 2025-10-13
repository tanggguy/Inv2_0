# 🏗️ Architecture Complète - Paper Trading avec Alpaca

## Vue d'ensemble du système

```
┌─────────────────────────────────────────────────────────────────┐
│                        PAPER TRADING ENGINE                      │
│                          (Coordinateur)                          │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             ▼                                    ▼
┌────────────────────────┐          ┌────────────────────────────┐
│    ALPACA STORE        │          │   MULTI-STRATEGY RUNNER     │
│  (Connexion API)       │◄─────────┤   (Gestion stratégies)      │
└──────────┬─────────────┘          └────────────┬───────────────┘
           │                                      │
           ▼                                      ▼
┌────────────────────────┐          ┌────────────────────────────┐
│   ALPACA BROKER        │          │      STRATEGIES             │
│  (Exécution ordres)    │          │  (MovingAverage, RSI, etc) │
└────────────────────────┘          └────────────────────────────┘
           │                                      │
           ▼                                      ▼
┌────────────────────────┐          ┌────────────────────────────┐
│    ALPACA DATA         │          │    CIRCUIT BREAKER          │
│  (Données temps réel)  │          │   (Protection capital)      │
└────────────────────────┘          └────────────────────────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
              ┌────────────────────────┐
              │  PORTFOLIO STATE MGR   │
              │    (Sauvegarde état)   │
              └────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  TELEGRAM NOTIFIER     │
              │    (Notifications)     │
              └────────────────────────┘
```

## Flux d'exécution détaillé

### 1. Initialisation (PaperTradingEngine)
```python
engine = PaperTradingEngine()
engine.initialize()
```
- ✅ Charge la configuration depuis `paper_trading_config.py`
- ✅ Valide les clés API Alpaca
- ✅ Initialise tous les composants
- ✅ Restaure l'état précédent si disponible

### 2. Connexion Alpaca (AlpacaStore)
```python
store = AlpacaStore(api_key, secret_key)
```
- ✅ Authentification avec l'API Alpaca
- ✅ Connexion WebSocket pour données temps réel
- ✅ Cache des données de marché
- ✅ Gestion reconnexion automatique

### 3. Chargement des Stratégies (MultiStrategyRunner)
```python
runner = MultiStrategyRunner(config, store)
runner.initialize()
```
Pour chaque stratégie active:
- ✅ Crée une instance Cerebro séparée
- ✅ Alloue le capital défini
- ✅ Charge les symboles à trader
- ✅ Configure les paramètres

### 4. Flux de Données (AlpacaData)
```python
data = AlpacaData(store, symbol='AAPL')
```
- ✅ Charge l'historique (100 jours par défaut)
- ✅ S'abonne au WebSocket pour temps réel
- ✅ Buffer les données pour Backtrader
- ✅ Conversion format Alpaca → Backtrader

### 5. Exécution des Stratégies
Chaque stratégie dans son thread:
```python
strategy.next()  # Appelé à chaque nouvelle barre
```
1. Vérification circuit breaker
2. Calcul des indicateurs
3. Génération des signaux
4. Passage des ordres si conditions remplies

### 6. Gestion des Ordres (AlpacaBroker)
```python
broker.buy(size=100)  # Ordre d'achat
```
- ✅ Validation des limites de risque
- ✅ Soumission à Alpaca API
- ✅ Tracking du statut (filled, partial, rejected)
- ✅ Mise à jour des positions

### 7. Circuit Breakers (CircuitBreaker)
Vérification continue:
- ❌ Drawdown > 20% → PAUSE
- ❌ Pertes jour > 5% → PAUSE
- ❌ 5 pertes consécutives → PAUSE
- ❌ > 50 trades/jour → PAUSE

### 8. Sauvegarde État (PortfolioStateManager)
Toutes les 5 minutes:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "account": {
    "value": 98500,
    "cash": 45000,
    "positions": {...}
  },
  "strategies": {...},
  "performance": {...}
}
```

### 9. Notifications (TelegramNotifier)
Événements notifiés:
- 📈 Trade exécuté
- 🚨 Circuit breaker déclenché
- 📊 Résumé quotidien
- ❌ Erreur système

## Cycle de vie d'un Trade

```
1. SIGNAL GÉNÉRÉ
   └─> Stratégie détecte opportunité
   
2. VÉRIFICATION RISQUES
   └─> Circuit breaker valide
   
3. ORDRE CRÉÉ
   └─> AlpacaBroker.buy(100 AAPL)
   
4. SOUMISSION API
   └─> AlpacaStore.submit_order()
   
5. CONFIRMATION
   └─> WebSocket: ordre accepté
   
6. EXÉCUTION
   └─> WebSocket: ordre exécuté @ $150.25
   
7. MISE À JOUR
   ├─> Position mise à jour
   ├─> Cash débité
   └─> État sauvegardé
   
8. NOTIFICATION
   └─> Telegram: "📈 Acheté 100 AAPL @ $150.25"
```

## Configuration Complète

### Structure des Fichiers
```
trading_system/
│
├── paper_trading/           # MODULE PRINCIPAL
│   ├── __init__.py
│   ├── paper_engine.py      # Coordinateur principal
│   ├── alpaca_store.py      # Gestion API Alpaca
│   ├── alpaca_broker.py     # Exécution ordres
│   ├── alpaca_data.py       # Données temps réel
│   ├── portfolio_state.py   # Persistance état
│   ├── circuit_breaker.py   # Protection capital
│   ├── multi_strategy_runner.py # Multi-stratégies
│   └── README.md            # Documentation
│
├── config/
│   ├── paper_trading_config.py  # Config paper trading
│   └── settings.py              # Config globale
│
├── strategies/
│   ├── base_strategy.py    # Classe de base
│   ├── moving_average.py   # Stratégie MA
│   ├── rsi_strategy.py     # Stratégie RSI
│   └── advanced_strategies.py # Stratégies avancées
│
├── monitoring/
│   ├── logger.py           # Système de logs
│   └── telegram_notifier.py # Notifications
│
├── data_cache/
│   └── portfolio_states/   # Sauvegardes état
│       ├── latest_state.json
│       └── portfolio_state_*.json.gz
│
├── logs/
│   ├── paper_engine.log
│   ├── alpaca_store.log
│   └── circuit_breaker.log
│
├── main.py                 # Point d'entrée principal
├── start_paper_trading.py  # Démarrage rapide
├── check_installation.py   # Vérification installation
├── requirements.txt        # Dépendances Python
├── .env.example           # Template configuration
└── .env                   # Configuration (ignoré git)
```

## Commandes de Gestion

### Démarrage
```bash
# Standard
python start_paper_trading.py

# Avec restauration
python start_paper_trading.py --restore

# Mode verbose
python start_paper_trading.py --verbose
```

### Monitoring
```bash
# Logs en temps réel
tail -f logs/paper_engine.log

# État actuel
cat data_cache/portfolio_states/latest_state.json | jq

# Performance
grep "P&L" logs/paper_engine.log | tail -10
```

### Maintenance
```bash
# Nettoyer anciens backups
find data_cache/portfolio_states -mtime +30 -delete

# Backup complet
tar -czf backup_$(date +%Y%m%d).tar.gz data_cache/

# Reset complet
rm -rf data_cache/portfolio_states/*
rm -f logs/*.log
```

## Points Clés de Sécurité

### ✅ Protections Implémentées

1. **Circuit Breakers Automatiques**
   - Arrêt si drawdown excessif
   - Limite de trades quotidiens
   - Pause après pertes consécutives

2. **Validation des Ordres**
   - Taille position max 25%
   - Vérification capital disponible
   - Heures de marché uniquement

3. **Sauvegarde Continue**
   - État sauvé toutes les 5 min
   - Backup rotatif (100 fichiers max)
   - Compression des anciens états

4. **Gestion d'Erreurs**
   - Reconnexion automatique
   - Notifications d'erreur
   - Logs détaillés

### ⚠️ Limites du Paper Trading

1. **Exécution Parfaite**
   - Pas de slippage réel
   - Liquidité illimitée
   - Prix exact garanti

2. **Psychologie Différente**
   - Pas de stress financier
   - Décisions plus risquées
   - Émotions absentes

3. **Conditions Idéales**
   - Pas de problèmes techniques
   - Données toujours disponibles
   - Ordres toujours acceptés

## Optimisation et Tuning

### Paramètres à Ajuster

1. **Timeframe des Données**
```python
"data": {
    "timeframe": "15M",  # 15 minutes au lieu d'1H
}
```

2. **Allocation de Capital**
```python
"strategies": [{
    "capital_allocation": 25000,  # Réduire pour tester
}]
```

3. **Circuit Breakers**
```python
"circuit_breakers": {
    "max_drawdown_pct": 0.10,  # Plus conservateur
}
```

### Métriques à Surveiller

- **Sharpe Ratio** > 1.5 (bon)
- **Win Rate** > 50% (positif)
- **Max Drawdown** < 15% (acceptable)
- **Trades/Jour** < 20 (raisonnable)

## Migration vers Live Trading

### Checklist Avant Live

- [ ] 3+ mois de paper trading profitable
- [ ] Sharpe Ratio > 2.0
- [ ] Drawdown max < 10%
- [ ] Stratégie stable (pas de modifications récentes)
- [ ] Capital de départ = 10% du paper trading
- [ ] Circuit breakers renforcés
- [ ] Monitoring 24/7 configuré
- [ ] Plan de sortie défini

### Changements Nécessaires

1. **URL API**
```python
ALPACA_BASE_URL=https://api.alpaca.markets  # LIVE
```

2. **Circuit Breakers Plus Stricts**
```python
"max_drawdown_pct": 0.05,  # 5% seulement
"max_daily_loss_pct": 0.02,  # 2% max/jour
```

3. **Notifications Critiques**
```python
"telegram_on_all_trades": True,
"telegram_on_any_error": True,
```

## Support et Ressources

- 📚 [Documentation Alpaca](https://docs.alpaca.markets/)
- 💬 [Discord Alpaca](https://discord.gg/alpaca)
- 📖 [Backtrader Docs](https://www.backtrader.com/)
- 🐍 [Code Examples](https://github.com/alpacahq/alpaca-py)

---

**🎯 Objectif:** Système robuste de paper trading pour tester et valider des stratégies avant le trading réel.

**⚡ Performance:** Capable de gérer 5+ stratégies simultanément avec données temps réel.

**🛡️ Sécurité:** Multiple couches de protection pour préserver le capital.