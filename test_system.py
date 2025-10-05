#!/usr/bin/env python3
"""
Script de test complet du système
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from data.data_handler import DataHandler
from monitoring.logger import setup_logger

logger = setup_logger("test_system")


def test_configuration():
    """Test du chargement de la configuration"""
    print("\n" + "="*60)
    print("TEST 1: Configuration")
    print("="*60)
    
    try:
        config = settings.get_config()
        print(f"✓ Mode de trading: {config['trading_mode']}")
        print(f"✓ Capital initial: ${config['initial_capital']:,.2f}")
        print(f"✓ Commission: {config['commission']*100}%")
        print("✅ Configuration OK")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_data_handler():
    """Test du gestionnaire de données"""
    print("\n" + "="*60)
    print("TEST 2: Data Handler")
    print("="*60)
    
    try:
        handler = DataHandler()
        print("✓ DataHandler initialisé")
        
        # Test téléchargement
        df = handler.fetch_data("AAPL", "2024-01-01", "2024-01-31")
        
        if df is not None and not df.empty:
            print(f"✓ Données téléchargées: {len(df)} barres")
            print(f"✓ Colonnes: {list(df.columns)}")
            print(f"✓ Période: {df.index[0]} → {df.index[-1]}")
            print("✅ Data Handler OK")
            return True
        else:
            print("⚠️  Aucune donnée récupérée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_strategies():
    """Test du chargement des stratégies"""
    print("\n" + "="*60)
    print("TEST 3: Stratégies")
    print("="*60)
    
    try:
        from strategies.moving_average import MovingAverageStrategy
        from strategies.rsi_strategy import RSIStrategy
        
        print("✓ MovingAverageStrategy chargée")
        print("✓ RSIStrategy chargée")
        print("✅ Stratégies OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_backtest_engine():
    """Test du moteur de backtesting"""
    print("\n" + "="*60)
    print("TEST 4: Backtest Engine")
    print("="*60)
    
    try:
        from backtesting.backtest_engine import BacktestEngine
        
        print("✓ BacktestEngine importé")
        
        # Test simple
        engine = BacktestEngine(
            strategy_name="MovingAverage",
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=10000
        )
        
        print("✓ BacktestEngine initialisé")
        print("✅ Backtest Engine OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_risk_management():
    """Test de la gestion des risques"""
    print("\n" + "="*60)
    print("TEST 5: Risk Management")
    print("="*60)
    
    try:
        from risk_management.risk_manager import RiskManager
        
        rm = RiskManager()
        print("✓ RiskManager initialisé")
        
        # Test validation position
        adjusted = rm.validate_position_size(100, 150, 100000)
        print(f"✓ Validation position: {adjusted} actions")
        
        # Test calcul stop loss
        stop = rm.calculate_stop_loss(100)
        print(f"✓ Stop loss calculé: ${stop:.2f}")
        
        print("✅ Risk Management OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("🧪 TESTS DU SYSTÈME DE TRADING")
    print("="*60)
    
    results = []
    
    results.append(("Configuration", test_configuration()))
    results.append(("Data Handler", test_data_handler()))
    results.append(("Stratégies", test_strategies()))
    results.append(("Backtest Engine", test_backtest_engine()))
    results.append(("Risk Management", test_risk_management()))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print("="*60)
    print(f"Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés ! Le système est prêt.")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
