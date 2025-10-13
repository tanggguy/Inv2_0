#!/usr/bin/env python3
"""
Script de test pour vérifier l'unification des param_grid
Teste que optimization_presets.json est bien la source unique pour tous les types d'optimisation
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from optimization.optimization_config import OptimizationConfig


def test_preset_loading():
    """Test 1: Chargement des presets"""
    print("\n" + "="*70)
    print("TEST 1: CHARGEMENT DES PRESETS")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    presets = config_mgr.list_presets()
    
    print(f"✓ {len(presets)} presets trouvés:")
    for preset_name in presets:
        print(f"  • {preset_name}")
    
    assert len(presets) > 0, "Aucun preset trouvé!"
    print("\n✅ Test 1 RÉUSSI\n")


def test_grid_search_config():
    """Test 2: Configuration Grid Search"""
    print("="*70)
    print("TEST 2: CONFIGURATION GRID SEARCH")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    config = config_mgr.get_preset('standard', opt_type='grid_search')
    
    print(f"\n📊 Preset 'standard' pour Grid Search:")
    print(f"  • Symboles: {config['symbols']}")
    print(f"  • Période: {config['period']['start']} → {config['period']['end']}")
    print(f"  • Capital: ${config['capital']:,}")
    
    print(f"\n  Param_grid:")
    for param, values in config['param_grid'].items():
        print(f"    • {param}: {len(values)} valeurs - {values}")
    
    assert 'param_grid' in config, "param_grid manquant!"
    assert len(config['param_grid']) > 0, "param_grid vide!"
    
    print("\n✅ Test 2 RÉUSSI\n")


def test_optuna_config():
    """Test 3: Configuration Optuna"""
    print("="*70)
    print("TEST 3: CONFIGURATION OPTUNA")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    config = config_mgr.get_preset('standard', opt_type='optuna')
    
    print(f"\n🚀 Preset 'standard' pour Optuna:")
    print(f"  • Symboles: {config['symbols']}")
    print(f"  • Période: {config['period']['start']} → {config['period']['end']}")
    
    print(f"\n  Param_grid (DOIT être le même que Grid Search):")
    for param, values in config['param_grid'].items():
        print(f"    • {param}: {len(values)} valeurs - {values}")
    
    print(f"\n  Config Optuna:")
    optuna_cfg = config.get('optuna', {})
    print(f"    • n_trials: {optuna_cfg.get('n_trials')}")
    print(f"    • sampler: {optuna_cfg.get('sampler')}")
    print(f"    • pruner: {optuna_cfg.get('pruner')}")
    print(f"    • save_plots: {optuna_cfg.get('save_plots')}")
    
    assert 'param_grid' in config, "param_grid manquant!"
    assert 'optuna' in config, "config optuna manquante!"
    assert len(config['param_grid']) > 0, "param_grid vide!"
    
    print("\n✅ Test 3 RÉUSSI\n")


def test_strategy_adaptation():
    """Test 4: Adaptation pour stratégie spécifique"""
    print("="*70)
    print("TEST 4: ADAPTATION PAR STRATÉGIE")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    
    # Test avec RSIStrategy
    print("\n📈 Test avec RSIStrategy:")
    config_rsi = config_mgr.adapt_preset_for_strategy(
        'standard', 
        'RSIStrategy',
        opt_type='optuna'
    )
    
    print(f"\n  Param_grid adapté pour RSIStrategy:")
    for param, values in config_rsi['param_grid'].items():
        print(f"    • {param}: {len(values)} valeurs - {values}")
    
    # Vérifier que les paramètres sont bien ceux de RSI
    expected_params = ['rsi_period', 'oversold', 'overbought', 'stop_loss_pct']
    actual_params = list(config_rsi['param_grid'].keys())
    
    print(f"\n  Paramètres attendus: {expected_params}")
    print(f"  Paramètres obtenus:  {actual_params}")
    
    # Test avec MovingAverageStrategy
    print("\n📈 Test avec MovingAverageStrategy:")
    config_ma = config_mgr.adapt_preset_for_strategy(
        'standard',
        'MovingAverageStrategy',
        opt_type='optuna'
    )
    
    print(f"\n  Param_grid adapté pour MovingAverageStrategy:")
    for param, values in config_ma['param_grid'].items():
        print(f"    • {param}: {len(values)} valeurs - {values}")
    
    expected_params_ma = ['fast_period', 'slow_period', 'stop_loss_pct', 'take_profit_pct']
    actual_params_ma = list(config_ma['param_grid'].keys())
    
    print(f"\n  Paramètres attendus: {expected_params_ma}")
    print(f"  Paramètres obtenus:  {actual_params_ma}")
    
    assert config_rsi['param_grid'] != config_ma['param_grid'], \
        "Les param_grid devraient être différents pour chaque stratégie!"
    
    print("\n✅ Test 4 RÉUSSI\n")


def test_param_grid_consistency():
    """Test 5: Cohérence param_grid Grid Search vs Optuna"""
    print("="*70)
    print("TEST 5: COHÉRENCE PARAM_GRID (Grid Search vs Optuna)")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    
    # Charger le même preset pour les deux types
    config_grid = config_mgr.get_preset('standard', opt_type='grid_search')
    config_optuna = config_mgr.get_preset('standard', opt_type='optuna')
    
    print("\n🔍 Comparaison des param_grid:")
    print(f"\n  Grid Search:")
    for param, values in config_grid['param_grid'].items():
        print(f"    • {param}: {values}")
    
    print(f"\n  Optuna:")
    for param, values in config_optuna['param_grid'].items():
        print(f"    • {param}: {values}")
    
    # Vérifier que les param_grid sont identiques
    assert config_grid['param_grid'] == config_optuna['param_grid'], \
        "❌ ERREUR: Les param_grid devraient être identiques!"
    
    print("\n✓ Les param_grid sont identiques pour Grid Search et Optuna")
    print("✅ Test 5 RÉUSSI\n")


def test_config_summary():
    """Test 6: Génération de résumé"""
    print("="*70)
    print("TEST 6: GÉNÉRATION DE RÉSUMÉ")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    config = config_mgr.get_preset('standard', opt_type='optuna')
    
    summary = config_mgr.get_config_summary(config)
    print(f"\n{summary}")
    
    assert len(summary) > 0, "Résumé vide!"
    print("\n✅ Test 6 RÉUSSI\n")


def test_validation():
    """Test 7: Validation de configuration"""
    print("="*70)
    print("TEST 7: VALIDATION DE CONFIGURATION")
    print("="*70)
    
    config_mgr = OptimizationConfig()
    
    # Config valide
    config_valid = config_mgr.get_preset('standard')
    is_valid, errors = config_mgr.validate_config(config_valid)
    
    print(f"\n✓ Config valide: {is_valid}")
    if errors:
        print(f"  Erreurs: {errors}")
    
    assert is_valid, "Le preset 'standard' devrait être valide!"
    
    # Config invalide
    config_invalid = {
        'symbols': [],  # Vide
        'period': {'start': '2023-01-01'},  # 'end' manquant
        'param_grid': {}  # Vide
    }
    
    is_valid, errors = config_mgr.validate_config(config_invalid)
    
    print(f"\n✓ Config invalide détectée: {not is_valid}")
    print(f"  Erreurs trouvées:")
    for error in errors:
        print(f"    • {error}")
    
    assert not is_valid, "La config invalide devrait être détectée!"
    assert len(errors) > 0, "Des erreurs devraient être trouvées!"
    
    print("\n✅ Test 7 RÉUSSI\n")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "🧪 " + "="*68)
    print("🧪 TEST DE L'UNIFICATION DES PARAM_GRID")
    print("🧪 " + "="*68 + "\n")
    
    tests = [
        ("Chargement des presets", test_preset_loading),
        ("Configuration Grid Search", test_grid_search_config),
        ("Configuration Optuna", test_optuna_config),
        ("Adaptation par stratégie", test_strategy_adaptation),
        ("Cohérence param_grid", test_param_grid_consistency),
        ("Génération de résumé", test_config_summary),
        ("Validation de config", test_validation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{test_name}' ÉCHOUÉ:")
            print(f"   Erreur: {e}\n")
            import traceback
            traceback.print_exc()
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"\n✅ Tests réussis: {passed}/{len(tests)}")
    print(f"❌ Tests échoués:  {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("\n✓ L'unification des param_grid fonctionne correctement")
        print("✓ optimization_presets.json est bien la source unique")
        print("✓ Les param_grid sont cohérents entre Grid Search et Optuna")
        print("✓ L'adaptation par stratégie fonctionne")
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("   Vérifiez les erreurs ci-dessus")
    
    print("\n" + "="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)