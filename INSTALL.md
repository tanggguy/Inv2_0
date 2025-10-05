# 📦 Guide d'Installation Complet

## Prérequis

- Python 3.9+ (recommandé 3.10 ou 3.11)
- pip (gestionnaire de paquets Python)
- git (optionnel)

## 🚀 Installation Pas à Pas

### Étape 1: Créer l'environnement virtuel

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Linux/Mac:
source venv/bin/activate

# Sur Windows:
venv\Scripts\activate
```

### Étape 2: Générer la structure du projet

```bash
# Exécuter le script de setup
python setup_project.py

# Créer les modules
python create_modules.py

# Créer les modules de backtesting
python create_backtest_modules.py

# Créer les utilitaires
python create_utilities.py
```

### Étape 3: Installer les dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 4: Installation de TA-Lib (Optionnel mais recommandé)

#### Sur Windows:
1. Télécharger le wheel depuis: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
2. Installer: `pip install TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl`

#### Sur Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

#### Sur Mac:
```bash
brew install ta-lib
pip install TA-Lib
```

### Étape 5: Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres
nano .env  # ou votre éditeur préféré
```

### Étape 6: Tester l'installation

```bash
# Exécuter les tests
python test_system.py

# Ou via main.py
python main.py --test
```

## ✅ Vérification

Si tous les tests passent, vous devriez voir:

```
🎉 Tous les tests sont passés ! Le système est prêt.
```

## 🎯 Premier Backtest

```bash
# Lancer un backtest simple
python main.py --mode backtest --strategy MovingAverage --symbols AAPL
```

## 🔧 Résolution de Problèmes

### Erreur: "No module named 'backtrader'"
```bash
pip install backtrader
```

### Erreur: "No module named 'yfinance'"
```bash
pip install yfinance
```

### Erreur de téléchargement de données
- Vérifiez votre connexion internet
- Vérifiez que le symbole est correct
- Essayez avec des dates plus récentes

### TA-Lib ne s'installe pas
- Sur Windows, utilisez le wheel pré-compilé
- Sur Linux, installez les dépendances système d'abord
- TA-Lib est optionnel, le système fonctionne sans

## 📚 Ressources

- Documentation Backtrader: https://www.backtrader.com/
- Yahoo Finance: https://finance.yahoo.com/
- Support: Ouvrir une issue sur GitHub

## 🎓 Prochaines Étapes

1. Lire le README.md
2. Explorer les stratégies dans `strategies/`
3. Personnaliser les paramètres dans `config/settings.py`
4. Créer votre première stratégie
5. Lancer des backtests

Bon trading ! 🚀
