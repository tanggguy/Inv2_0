#!/usr/bin/env python3
"""
Gestionnaire de configuration pour les optimisations
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
# Import différé du logger pour éviter l'importation circulaire
_logger = None

def _get_logger():
    """Récupère le logger de manière différée"""
    global _logger
    if _logger is None:
        from monitoring.logger import setup_logger
        _logger = setup_logger("optimization_config")
    return _logger


class OptimizationConfig:
    """Gère les configurations d'optimisation"""
    
    PRESETS_FILE = Path(__file__).parent.parent / "config" / "optimization_presets.json"
    
    def __init__(self):
        self.presets = self._load_presets()
    
    def _load_presets(self) -> Dict:
        """Charge les presets depuis le fichier JSON"""
        try:
            with open(self.PRESETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _get_logger().info(f"✓ {len(data.get('presets', {}))} presets chargés")
            return data
        except FileNotFoundError:
            _get_logger().error(f"Fichier de presets introuvable: {self.PRESETS_FILE}")
            return {"presets": {}, "strategy_defaults": {}}
        except json.JSONDecodeError as e:
            _get_logger().error(f"Erreur de parsing JSON: {e}")
            return {"presets": {}, "strategy_defaults": {}}
    
    def get_preset(self, name: str) -> Optional[Dict]:
        """
        Récupère un preset par son nom
        
        Args:
            name: Nom du preset (ex: 'quick', 'standard', 'exhaustive')
        
        Returns:
            Dict avec la configuration ou None si introuvable
        """
        preset = self.presets.get('presets', {}).get(name)
        if preset:
            _get_logger().info(f"Preset '{name}' chargé: {preset.get('description', '')}")
            return preset.copy()
        else:
            _get_logger().warning(f"Preset '{name}' introuvable")
            return None
    
    def list_presets(self) -> List[str]:
        """Liste tous les presets disponibles"""
        return list(self.presets.get('presets', {}).keys())
    
    def get_strategy_defaults(self, strategy_name: str) -> Optional[Dict]:
        """
        Récupère les paramètres par défaut pour une stratégie
        
        Args:
            strategy_name: Nom de la stratégie
        
        Returns:
            Dict avec param_grid par défaut ou None
        """
        defaults = self.presets.get('strategy_defaults', {}).get(strategy_name)
        if defaults:
            _get_logger().info(f"Paramètres par défaut chargés pour {strategy_name}")
            return defaults.copy()
        else:
            _get_logger().warning(f"Pas de paramètres par défaut pour {strategy_name}")
            return None
        
    def get_config_for_strategy(self, 
                                strategy_name: str, 
                                preset_name: str = "standard",
                                override_params: bool = True) -> Dict:
        """
        Charge un preset et l'adapte automatiquement à une stratégie spécifique
        
        Cette méthode fusionne:
        - Les paramètres généraux du preset (symbols, period, capital, walk_forward)
        - La grille de paramètres spécifique à la stratégie (param_grid)
        
        Args:
            strategy_name: Nom de la stratégie (ex: 'MovingAverage', 'RSI', 'MaSuperStrategie')
            preset_name: Nom du preset (ex: 'standard', 'quick', 'exhaustive')
            override_params: Si True, remplace param_grid par strategy_defaults
        
        Returns:
            Configuration fusionnée adaptée à la stratégie
        
        Exemple:
            >>> config = manager.get_config_for_strategy('MovingAverage', 'standard')
            >>> # config aura les symbols/period du preset 'standard'
            >>> # mais le param_grid de MovingAverage (fast_period, slow_period)
        """
        # 1. Charger le preset de base (pour symbols, period, capital, walk_forward)
        config = self.get_preset(preset_name)
        
        if not config:
            raise ValueError(f"Preset '{preset_name}' introuvable. Disponibles: {self.list_presets()}")
        
        # 2. Chercher les paramètres par défaut de la stratégie
        strategy_defaults = self.get_strategy_defaults(strategy_name)
        
        # 3. Fusionner si des paramètres spécifiques existent
        if strategy_defaults and override_params:
            strategy_param_grid = strategy_defaults.get('param_grid', {})
            
            if strategy_param_grid:
                # Remplacer le param_grid par celui de la stratégie
                old_param_grid = config.get('param_grid', {})
                config['param_grid'] = strategy_param_grid
                
                _get_logger().info(
                    f"✓ Param_grid adapté pour {strategy_name}: "
                    f"{list(old_param_grid.keys())} → {list(strategy_param_grid.keys())}"
                )
            else:
                _get_logger().warning(
                    f"⚠️ strategy_defaults trouvé pour {strategy_name} mais param_grid vide"
                )
        else:
            # Pas de strategy_defaults, garder le param_grid du preset
            _get_logger().warning(
                f"⚠️ Aucun strategy_defaults pour '{strategy_name}'. "
                f"Utilisation du param_grid du preset '{preset_name}'. "
                f"Les paramètres peuvent ne pas correspondre à la stratégie."
            )
        
        # 4. Ajouter des métadonnées pour traçabilité
        config['_metadata'] = {
            'strategy_name': strategy_name,
            'preset_name': preset_name,
            'adapted': bool(strategy_defaults and override_params),
            'timestamp': datetime.now().isoformat()
        }
        
        return config    
    def validate_strategy_params(self, strategy_class, param_grid: Dict) -> tuple[bool, List[str]]:
        """
        Validation basique des paramètres (non-bloquante)
        
        Args:
            strategy_class: Classe de la stratégie
            param_grid: Grille de paramètres
        
        Returns:
            (True, list_of_info_messages)
        """
        info_messages = []
        
        # Juste logger les infos, jamais bloquer
        try:
            if hasattr(strategy_class, 'params'):
                info_messages.append(
                    f"ℹ️ Validation de {strategy_class.__name__} avec "
                    f"{len(param_grid)} paramètres à optimiser: {list(param_grid.keys())}"
                )
            else:
                info_messages.append(
                    f"ℹ️ {strategy_class.__name__} : structure de params non standard"
                )
        except Exception as e:
            info_messages.append(f"ℹ️ Validation ignorée: {e}")
        
        # Toujours retourner True pour ne jamais bloquer
        return True, info_messages
    def create_custom(self, 
                     symbols: List[str],
                     start_date: str,
                     end_date: str,
                     param_grid: Dict,
                     capital: float = 100000,
                     name: str = "Custom",
                     description: str = "") -> Dict:
        """
        Crée une configuration personnalisée
        
        Args:
            symbols: Liste des symboles
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)
            param_grid: Grille de paramètres
            capital: Capital initial
            name: Nom de la config
            description: Description
        
        Returns:
            Dict de configuration
        """
        config = {
            "name": name,
            "description": description or f"Config custom créée le {datetime.now().strftime('%Y-%m-%d')}",
            "symbols": symbols,
            "period": {
                "start": start_date,
                "end": end_date
            },
            "capital": capital,
            "param_grid": param_grid
        }
        
        _get_logger().info(f"Configuration custom créée: {name}")
        return config
    
    def merge_configs(self, base_preset: str, overrides: Dict) -> Dict:
        """
        Fusionne un preset avec des overrides
        
        Args:
            base_preset: Nom du preset de base
            overrides: Dict avec les valeurs à override
        
        Returns:
            Configuration fusionnée
        """
        config = self.get_preset(base_preset)
        if not config:
            raise ValueError(f"Preset '{base_preset}' introuvable")
        
        # Fusion récursive
        def deep_merge(base, override):
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        merged = deep_merge(config, overrides)
        _get_logger().info(f"Config fusionnée: {base_preset} + overrides")
        return merged
    
    def validate_config(self, config: Dict,strategy_class=None) -> tuple[bool, List[str]]:
        """
        Valide une configuration
        
        Args:
            config: Configuration à valider
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Vérifications obligatoires
        required_fields = ['symbols', 'period', 'param_grid']
        for field in required_fields:
            if field not in config:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        # Vérifier period
        if 'period' in config:
            if 'start' not in config['period'] or 'end' not in config['period']:
                errors.append("Period doit contenir 'start' et 'end'")
            else:
                try:
                    start = datetime.strptime(config['period']['start'], '%Y-%m-%d')
                    end = datetime.strptime(config['period']['end'], '%Y-%m-%d')
                    if start >= end:
                        errors.append("Date de début doit être avant date de fin")
                except ValueError:
                    errors.append("Format de date invalide (utilisez YYYY-MM-DD)")
        
        # Vérifier symbols
        if 'symbols' in config and not config['symbols']:
            errors.append("La liste de symboles ne peut pas être vide")
        
        # Vérifier param_grid
        if 'param_grid' in config:
            if not config['param_grid']:
                errors.append("param_grid ne peut pas être vide")
            else:
                for param, values in config['param_grid'].items():
                    if not isinstance(values, list) or not values:
                        errors.append(f"param_grid['{param}'] doit être une liste non vide")

        if strategy_class and 'param_grid' in config:
            is_params_valid, param_warnings = self.validate_strategy_params(
            strategy_class, 
            config['param_grid']
            )
            if not is_params_valid:
                errors.extend(param_warnings)
    
    
        is_valid = len(errors) == 0
        
        if is_valid:
            _get_logger().info("✓ Configuration valide")
        else:
            _get_logger().warning(f"Configuration invalide: {', '.join(errors)}")
        
        return is_valid, errors
    
    def save_preset(self, name: str, config: Dict) -> bool:
        """
        Sauvegarde un nouveau preset dans le fichier JSON
        
        Args:
            name: Nom du preset
            config: Configuration à sauvegarder
        
        Returns:
            True si sauvegarde réussie
        """
        try:
            # Valider d'abord
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                _get_logger().error(f"Impossible de sauvegarder: {', '.join(errors)}")
                return False
            
            # Charger le fichier actuel
            with open(self.PRESETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ajouter le nouveau preset
            data['presets'][name] = config
            
            # Sauvegarder
            with open(self.PRESETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Recharger
            self.presets = data
            
            _get_logger().info(f"✓ Preset '{name}' sauvegardé avec succès")
            return True
            
        except Exception as e:
            _get_logger().error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def get_config_summary(self, config: Dict) -> str:
        """
        Génère un résumé textuel de la configuration
        
        Args:
            config: Configuration
        
        Returns:
            Résumé formaté
        """
        from itertools import product
        
        # Calculer le nombre de combinaisons
        total_combos = 1
        if 'param_grid' in config:
            for values in config['param_grid'].values():
                total_combos *= len(values)
        
        summary = f"""
Configuration: {config.get('name', 'Sans nom')}
{'='*60}
Description: {config.get('description', 'N/A')}

Symboles: {', '.join(config.get('symbols', []))}
Période: {config.get('period', {}).get('start')} → {config.get('period', {}).get('end')}
Capital: ${config.get('capital', 100000):,.2f}

Paramètres à tester:
{self._format_param_grid(config.get('param_grid', {}))}

Total combinaisons: {total_combos:,}

Walk-Forward: {'Oui' if 'walk_forward' in config else 'Non'}
{self._format_walk_forward(config.get('walk_forward')) if 'walk_forward' in config else ''}
"""
        return summary.strip()
    
    def _format_param_grid(self, param_grid: Dict) -> str:
        """Formate la grille de paramètres pour affichage"""
        lines = []
        for param, values in param_grid.items():
            lines.append(f"  • {param}: {values}")
        return '\n'.join(lines) if lines else "  Aucun"
    
    def _format_walk_forward(self, wf_config: Dict) -> str:
        """Formate la config walk-forward pour affichage"""
        if not wf_config:
            return ""
        
        return f"""  In-Sample: {wf_config.get('in_sample_months')} mois
  Out-Sample: {wf_config.get('out_sample_months')} mois"""


# Fonction helper pour usage simple
def load_preset(name: str) -> Dict:
    """
    Fonction helper pour charger rapidement un preset
    
    Args:
        name: Nom du preset
    
    Returns:
        Configuration du preset
    """
    config_manager = OptimizationConfig()
    preset = config_manager.get_preset(name)
    if not preset:
        raise ValueError(f"Preset '{name}' introuvable. Disponibles: {config_manager.list_presets()}")
    return preset


def get_strategy_params(strategy_name: str) -> Dict:
    """
    Fonction helper pour récupérer les paramètres par défaut d'une stratégie
    
    Args:
        strategy_name: Nom de la stratégie
    
    Returns:
        Param grid par défaut
    """
    config_manager = OptimizationConfig()
    defaults = config_manager.get_strategy_defaults(strategy_name)
    if not defaults:
        raise ValueError(f"Pas de paramètres par défaut pour '{strategy_name}'")
    return defaults.get('param_grid', {})


# Test du module
if __name__ == "__main__":
    print("="*70)
    print("TEST DU MODULE OPTIMIZATION CONFIG")
    print("="*70)
    
    config_manager = OptimizationConfig()
    
    # Lister les presets
    print("\n📋 Presets disponibles:")
    for preset_name in config_manager.list_presets():
        preset = config_manager.get_preset(preset_name)
        print(f"  • {preset_name}: {preset.get('description', 'N/A')}")
    
    # Charger et afficher un preset
    print("\n📊 Détails du preset 'standard':")
    print("="*70)
    standard_config = config_manager.get_preset('standard')
    print(config_manager.get_config_summary(standard_config))
    
    # Créer une config custom
    print("\n🔧 Création d'une config custom:")
    print("="*70)
    custom = config_manager.create_custom(
        symbols=['AAPL', 'TSLA'],
        start_date='2023-01-01',
        end_date='2024-01-01',
        param_grid={
            'ma_period': [10, 20, 30],
            'rsi_period': [14, 21]
        },
        name="Test Custom",
        description="Config de test"
    )
    print(config_manager.get_config_summary(custom))
    
    # Valider
    print("\n✅ Validation de la config custom:")
    is_valid, errors = config_manager.validate_config(custom)
    if is_valid:
        print("  ✓ Configuration valide !")
    else:
        print(f"  ✗ Erreurs: {errors}")
    
    # Merge
    print("\n🔀 Merge du preset 'quick' avec overrides:")
    print("="*70)
    merged = config_manager.merge_configs('quick', {
        'symbols': ['MSFT', 'GOOGL'],
        'param_grid': {
            'ma_period': [15, 25, 35]
        }
    })
    print(config_manager.get_config_summary(merged))
    
    print("\n✓ Tests terminés avec succès !")