#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    CORRECTIF: Erreur Float/Int dans Walk-Forward Optimization
═══════════════════════════════════════════════════════════════════════════════

Ce script corrige l'erreur "'float' object cannot be interpreted as an integer"
qui survient lors de l'optimisation Walk-Forward.

PROBLÈME:
- Les paramètres optimaux du Grid Search sont stockés en float (ex: 7.0)
- Backtrader attend des int pour les périodes (ex: 7)
- Erreur lors du passage au test Out-Sample

SOLUTION:
- Convertir automatiquement les float en int quand nécessaire
- Préserver les vrais float (ex: seuils, pourcentages)

UTILISATION:
1. Sauvegardez ce fichier dans votre projet
2. Exécutez: python fix_optimizer_float_error.py
3. Relancez votre optimisation Walk-Forward
"""

import re
from pathlib import Path


def create_param_converter():
    """Crée la fonction de conversion des paramètres"""
    return '''
    def _convert_params(self, params: Dict) -> Dict:
        """
        Convertit les paramètres float en int quand approprié
        
        Règles de conversion:
        - Les paramètres avec 'period', 'window', 'length' → int
        - Les paramètres entiers déguisés en float (14.0 → 14) → int
        - Les vrais float (0.5, 1.23) → conservés en float
        
        Args:
            params: Dictionnaire de paramètres
        
        Returns:
            Dictionnaire avec types corrigés
        """
        converted = {}
        
        for key, value in params.items():
            # Si ce n'est pas un nombre, garder tel quel
            if not isinstance(value, (int, float)):
                converted[key] = value
                continue
            
            # Règle 1: Les paramètres de période doivent être int
            period_keywords = ['period', 'window', 'length', 'span', 'lookback', 'days']
            if any(keyword in key.lower() for keyword in period_keywords):
                converted[key] = int(value)
                continue
            
            # Règle 2: Si c'est un float qui est en fait un entier (14.0 → 14)
            if isinstance(value, float) and value.is_integer():
                converted[key] = int(value)
            else:
                # Garder le type original
                converted[key] = value
        
        return converted
'''


def fix_optimizer_file(optimizer_path: Path):
    """Corrige le fichier optimizer.py"""
    
    print("═" * 70)
    print("🔧 CORRECTIF OPTIMIZER.PY")
    print("═" * 70)
    
    # Lire le fichier
    with open(optimizer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le correctif est déjà appliqué
    if '_convert_params' in content:
        print("✅ Le correctif est déjà appliqué!")
        return True
    
    print("📝 Application du correctif...\n")
    
    # 1. Ajouter la fonction _convert_params après __init__
    converter_code = create_param_converter()
    
    # Trouver la fin de __init__ et insérer la fonction
    init_pattern = r'(def __init__\(self.*?\n(?:.*?\n)*?.*?self\.run_id = .*?\n)'
    if re.search(init_pattern, content, re.DOTALL):
        content = re.sub(
            init_pattern,
            r'\1' + converter_code + '\n',
            content,
            count=1,
            flags=re.DOTALL
        )
        print("✓ Fonction _convert_params ajoutée")
    else:
        print("⚠️  Pattern __init__ non trouvé, ajout à la fin de la classe")
        # Fallback: ajouter après la première méthode
        content = content.replace(
            'def run(self',
            converter_code + '\n    def run(self'
        )
    
    # 2. Modifier _run_single_backtest pour utiliser _convert_params
    old_addstrategy = 'cerebro.addstrategy(self.strategy_class, **params, printlog=False)'
    new_addstrategy = '''# Convertir les paramètres (float → int si nécessaire)
            converted_params = self._convert_params(params)
            cerebro.addstrategy(self.strategy_class, **converted_params, printlog=False)'''
    
    if old_addstrategy in content:
        content = content.replace(old_addstrategy, new_addstrategy)
        print("✓ Appel _convert_params ajouté dans _run_single_backtest")
    else:
        print("⚠️  Ligne addstrategy non trouvée, vérification manuelle nécessaire")
    
    # 3. Sauvegarder avec backup
    backup_path = optimizer_path.with_suffix('.py.backup')
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(optimizer_path, 'r', encoding='utf-8') as original:
            f.write(original.read())
    
    print(f"✓ Backup créé: {backup_path}")
    
    # Écrire le fichier corrigé
    with open(optimizer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fichier corrigé: {optimizer_path}")
    
    print("\n" + "═" * 70)
    print("✅ CORRECTIF APPLIQUÉ AVEC SUCCÈS!")
    print("═" * 70)
    print("\n📋 Prochaines étapes:")
    print("  1. Vérifiez le fichier corrigé")
    print("  2. Relancez votre optimisation Walk-Forward")
    print("  3. L'erreur 'float' ne devrait plus apparaître\n")
    print("💡 En cas de problème, restaurez depuis le backup:")
    print(f"   cp {backup_path} {optimizer_path}\n")
    
    return True


def find_optimizer():
    """Trouve le fichier optimizer.py"""
    possible_paths = [
        Path("optimization/optimizer.py"),
        Path("optimisation/optimizer.py"),
        Path("../optimization/optimizer.py"),
        Path("../optimisation/optimizer.py"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.resolve()
    
    return None


def main():
    """Point d'entrée principal"""
    print("\n" + "═" * 70)
    print("🔍 RECHERCHE DU FICHIER OPTIMIZER.PY")
    print("═" * 70 + "\n")
    
    optimizer_path = find_optimizer()
    
    if not optimizer_path:
        print("❌ Fichier optimizer.py non trouvé!")
        print("\n📁 Chemins vérifiés:")
        print("  - optimization/optimizer.py")
        print("  - optimisation/optimizer.py")
        print("  - ../optimization/optimizer.py")
        print("  - ../optimisation/optimizer.py")
        print("\n💡 Solution:")
        print("  1. Naviguez vers le dossier racine de votre projet")
        print("  2. Relancez ce script depuis là")
        print("  OU")
        print("  3. Spécifiez le chemin manuellement:")
        print("     python fix_optimizer_float_error.py /chemin/vers/optimizer.py\n")
        return False
    
    print(f"✓ Fichier trouvé: {optimizer_path}\n")
    
    # Appliquer le correctif
    success = fix_optimizer_file(optimizer_path)
    
    if success:
        print("\n🎉 Correction terminée avec succès!")
        print("\n📊 Test rapide recommandé:")
        print("   python -c \"from optimization.optimizer import UnifiedOptimizer; print('✓ Import OK')\"")
    
    return success


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Chemin spécifié en argument
        optimizer_path = Path(sys.argv[1])
        if optimizer_path.exists():
            fix_optimizer_file(optimizer_path)
        else:
            print(f"❌ Fichier non trouvé: {optimizer_path}")
    else:
        # Recherche automatique
        main()