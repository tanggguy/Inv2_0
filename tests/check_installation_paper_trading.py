#!/usr/bin/env python3
"""
Script de vérification d'installation du Paper Trading
Vérifie que tous les composants sont correctement installés et configurés
"""

import sys
import os
from pathlib import Path
import importlib.util
import json
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_python_version():
    """Vérifie la version de Python"""
    print_header("Version Python")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ requis")
        return False

    print("✅ Version Python OK")
    return True


def check_required_packages():
    """Vérifie les packages Python requis"""
    print_header("Packages Requis")

    required = {
        "backtrader": "Trading framework",
        "pandas": "Data manipulation",
        "numpy": "Numerical computing",
        "dotenv": "Environment variables",
        "alpaca_trade_api": "Alpaca API client",
        "pytz": "Timezone support",
    }

    all_ok = True
    for package, description in required.items():
        module_name = package.replace("-", "_")
        if module_name == "dotenv":
            module_name = "dotenv"

        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"❌ {package:20} - {description} - NON INSTALLÉ")
            all_ok = False
        else:
            print(f"✅ {package:20} - {description}")

    return all_ok


def check_optional_packages():
    """Vérifie les packages optionnels"""
    print_header("Packages Optionnels")

    optional = {
        "telegram": "Notifications Telegram",
        "streamlit": "Dashboard web",
        "ta": "Technical Analysis",
        "scipy": "Optimisation",
        "pytest": "Tests unitaires",
    }

    for package, description in optional.items():
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"⚠️  {package:20} - {description} - Non installé (optionnel)")
        else:
            print(f"✅ {package:20} - {description}")


def check_project_structure():
    """Vérifie la structure du projet"""
    print_header("Structure du Projet")

    required_dirs = [
        "paper_trading",
        "config",
        "strategies",
        "monitoring",
        "data",
        "backtesting",
    ]

    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        "paper_trading/__init__.py",
        "paper_trading/paper_engine.py",
        "paper_trading/alpaca_store.py",
        "config/paper_trading_config.py",
    ]

    all_ok = True

    print("\nRépertoires:")
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - MANQUANT")
            all_ok = False

    print("\nFichiers principaux:")
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - MANQUANT")
            all_ok = False

    return all_ok


def check_environment_config():
    """Vérifie la configuration environnement"""
    print_header("Configuration Environnement")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_example.exists():
        print("❌ .env.example non trouvé")
        return False

    print("✅ .env.example trouvé")

    if not env_file.exists():
        print("⚠️  .env non trouvé - Créez-le depuis .env.example")
        print("   Commande: cp .env.example .env")
        return False

    print("✅ .env trouvé")

    # Charger et vérifier les variables
    from dotenv import load_dotenv

    load_dotenv()

    critical_vars = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
    ]

    optional_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    all_critical_ok = True

    print("\nVariables critiques:")
    for var in critical_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var:25} - Configuré")
        else:
            print(f"❌ {var:25} - NON CONFIGURÉ")
            all_critical_ok = False

    print("\nVariables optionnelles:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var:25} - Configuré")
        else:
            print(f"⚠️  {var:25} - Non configuré (optionnel)")

    return all_critical_ok


def test_imports():
    """Teste les imports du module paper trading"""
    print_header("Test des Imports")

    try:
        from paper_trading import PaperTradingEngine

        print("✅ PaperTradingEngine")

        from paper_trading import AlpacaStore

        print("✅ AlpacaStore")

        from paper_trading import CircuitBreaker

        print("✅ CircuitBreaker")

        from paper_trading import PortfolioStateManager

        print("✅ PortfolioStateManager")

        from config.paper_trading_config import PAPER_TRADING_CONFIG

        print("✅ Configuration")

        return True

    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_alpaca_connection():
    """Teste la connexion à Alpaca (si configuré)"""
    print_header("Test Connexion Alpaca")

    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        print("⚠️  Clés API non configurées - Test ignoré")
        return True

    try:
        import alpaca_trade_api as tradeapi

        api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url="https://paper-api.alpaca.markets",
            api_version="v2",
        )

        account = api.get_account()
        print(f"✅ Connexion réussie")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Pattern Day Trader: {account.pattern_day_trader}")

        return True

    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("   Vérifiez vos clés API")
        return False


def create_test_directories():
    """Crée les répertoires nécessaires"""
    print_header("Création des Répertoires")

    directories = [
        "logs",
        "data_cache",
        "data_cache/portfolio_states",
        "results",
        "tests",
    ]

    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✅ Créé: {dir_name}/")
        else:
            print(f"✅ Existe: {dir_name}/")

    return True


def generate_summary(results):
    """Génère un résumé des résultats"""
    print_header("RÉSUMÉ")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    print(f"\nTotal: {total} vérifications")
    print(f"✅ Réussies: {passed}")
    print(f"❌ Échouées: {failed}")

    if failed == 0:
        print("\n🎉 SYSTÈME PRÊT POUR LE PAPER TRADING! 🎉")
        print("\nPour démarrer:")
        print("  python start_paper_trading.py")
    else:
        print("\n⚠️  Corrigez les erreurs avant de continuer")
        print("\nProblèmes détectés:")
        for check, result in results.items():
            if not result:
                print(f"  ❌ {check}")

        print("\nActions recommandées:")
        if not results.get("packages", True):
            print("  1. pip install -r requirements.txt")
        if not results.get("environment", True):
            print("  2. cp .env.example .env && nano .env")
        if not results.get("structure", True):
            print("  3. Vérifiez que tous les fichiers sont présents")


def main():
    """Fonction principale"""
    print(
        """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     VÉRIFICATION D'INSTALLATION - PAPER TRADING         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    )

    results = {}

    # Vérifications
    results["python"] = check_python_version()
    results["packages"] = check_required_packages()
    check_optional_packages()  # Juste informatif
    results["structure"] = check_project_structure()
    results["environment"] = check_environment_config()
    results["imports"] = test_imports()
    results["directories"] = create_test_directories()

    # Test de connexion Alpaca (optionnel)
    if results["environment"]:
        test_alpaca_connection()  # Juste informatif

    # Résumé
    generate_summary(results)

    # Code de retour
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
