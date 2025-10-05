# ⚡ Guide de Démarrage Rapide

## Installation en 5 minutes

```bash
# 1. Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. Générer la structure
python setup_project.py
python create_modules.py
python create_backtest_modules.py
python create_utilities.py

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer
cp .env.example .env

# 5. Tester
python test_system.py
```

## Votre Premier Backtest (30 secondes)

```bash
python main.py --strategy MovingAverage --symbols AAPL --start-date 2023-01-01
```

## Exemples d'Utilisation

### Backtest Simple
```bash
python main.py --strategy MovingAverage --symbols AAPL
```

### Backtest Multi-Symboles
```bash
python main.py --strategy RSI --symbols AAPL MSFT GOOGL
```

### Backtest avec Période Personnalisée
```bash
python main.py --strategy MovingAverage --symbols TSLA \
  --start-date 2022-01-01 --end-date 2023-12-31
```

### Backtest avec Graphiques
```bash
python main.py --strategy RSI --symbols AAPL --plot
```

### Mode Verbose
```bash
python main.py --strategy MovingAverage --symbols AAPL --verbose
```

## Créer Votre Propre Stratégie

1. Copier `strategies/moving_average.py`
2. Renommer en `strategies/ma_strategie.py`
3. Modifier la logique dans `next()`
4. Tester: `python main.py --strategy MaStrategie --symbols AAPL`

## Fichiers Importants

- `config/settings.py` - Configuration globale
- `strategies/` - Vos stratégies
- `results/` - Rapports de backtest
- `logs/` - Fichiers de logs

## Commandes Utiles

```bash
# Tests complets
python test_system.py

# Test rapide
python main.py --test

# Aide
python main.py --help

# Liste des stratégies
ls strategies/*.py
```

## Prochaines Étapes

1. ✅ Installation complète
2. ✅ Premier backtest réussi
3. 📖 Lire INSTALL.md pour les détails
4. 🎯 Créer votre première stratégie
5. 📊 Analyser les résultats dans `results/`

Besoin d'aide ? Consultez README.md ou INSTALL.md

Happy Trading! 🎉
