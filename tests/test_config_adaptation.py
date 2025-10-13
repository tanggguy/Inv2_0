#!/usr/bin/env python3
"""Test de l'adaptation automatique des configurations"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimization.optimization_config import OptimizationConfig


def test_adaptation():
    config_manager = OptimizationConfig()

    strategies_to_test = ["MovingAverage", "RSI", "MaRSI", "MACrossoverAdvanced"]

    print("=" * 70)
    print("TEST D'ADAPTATION AUTOMATIQUE DES CONFIGURATIONS")
    print("=" * 70)

    for strategy_name in strategies_to_test:
        print(f"\n🎯 Test: {strategy_name}")
        print("-" * 70)

        # Charger avec adaptation
        config = config_manager.get_config_for_strategy(
            strategy_name=strategy_name, preset_name="standard"
        )

        # Vérifier
        param_grid = config.get("param_grid", {})
        adapted = config.get("_metadata", {}).get("adapted", False)

        print(f"  Adapté: {'✓' if adapted else '✗'}")
        print(f"  Paramètres: {list(param_grid.keys())}")

        # Comparer avec preset brut
        preset = config_manager.get_preset("standard")
        preset_params = list(preset.get("param_grid", {}).keys())
        config_params = list(param_grid.keys())

        if preset_params != config_params:
            print(f"  ✓ Param_grid modifié:")
            print(f"    Preset:  {preset_params}")
            print(f"    Adapté:  {config_params}")
        else:
            print(f"  ⚠️  Param_grid identique au preset")


if __name__ == "__main__":
    test_adaptation()
