#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    CRÉATEUR DE STRATÉGIE INTERACTIF
═══════════════════════════════════════════════════════════════════════════════

Script interactif pour créer une nouvelle stratégie facilement

Utilisation:
    python scripts/create_strategy.py

Le script vous guidera à travers toutes les étapes

Sauvegardez dans: scripts/create_strategy.py
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def print_banner():
    """Affiche le banner"""
    print(
        """
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║               🎨 CRÉATEUR DE STRATÉGIE INTERACTIF 🎨                 ║
║                                                                        ║
║            Créez votre stratégie de trading en quelques minutes       ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
    """
    )


def choose_template():
    """Permet de choisir un template"""
    print("\n" + "=" * 70)
    print("ÉTAPE 1: Choisir un template de départ")
    print("=" * 70)

    templates = {
        "1": {
            "name": "MyFirstStrategy",
            "description": "Template simple pour débuter (recommandé)",
            "difficulty": "⭐ Facile",
        },
        "2": {
            "name": "TripleIndicatorStrategy",
            "description": "MA + RSI + Volume (confirmation multiple)",
            "difficulty": "⭐⭐ Moyen",
        },
        "3": {
            "name": "ScalpingStrategy",
            "description": "Scalping avec stops serrés (court terme)",
            "difficulty": "⭐⭐⭐ Avancé",
        },
        "4": {
            "name": "SwingTradingStrategy",
            "description": "Swing trading (positions 2-10 jours)",
            "difficulty": "⭐⭐ Moyen",
        },
        "5": {
            "name": "MeanReversionStrategy",
            "description": "Retour à la moyenne avec Bollinger Bands",
            "difficulty": "⭐⭐ Moyen",
        },
        "6": {
            "name": "Blank",
            "description": "Vide - Démarrer from scratch",
            "difficulty": "⭐⭐⭐ Avancé",
        },
    }

    print("\nTemplates disponibles:\n")
    for key, template in templates.items():
        print(f"  {key}. {template['name']:<25} {template['difficulty']}")
        print(f"     → {template['description']}")
        print()

    while True:
        choice = input("Votre choix (1-6) [1]: ").strip() or "1"
        if choice in templates:
            return templates[choice]["name"]
        print("❌ Choix invalide. Veuillez choisir entre 1 et 6.")


def get_strategy_name():
    """Demande le nom de la stratégie"""
    print("\n" + "=" * 70)
    print("ÉTAPE 2: Nommer votre stratégie")
    print("=" * 70)

    print("\nConseil: Utilisez un nom descriptif en CamelCase")
    print("Exemples: MaSuperStrategie, RSIBreakout, TrendFollower")

    while True:
        name = input("\nNom de votre stratégie: ").strip()
        if not name:
            print("❌ Le nom ne peut pas être vide")
            continue

        # Vérifier le format
        if not name[0].isupper():
            print("⚠️  Le nom devrait commencer par une majuscule")
            confirm = input("Continuer quand même? (o/n) [o]: ").strip().lower() or "o"
            if confirm != "o":
                continue

        # Vérifier si le fichier existe déjà
        filepath = Path(f"strategies/{name.lower()}.py")
        if filepath.exists():
            print(f"⚠️  Le fichier {filepath} existe déjà")
            overwrite = input("Écraser? (o/n) [n]: ").strip().lower() or "n"
            if overwrite != "o":
                continue

        return name


def configure_stop_loss():
    """Configure le stop loss"""
    print("\n" + "=" * 70)
    print("ÉTAPE 3: Configuration du Stop Loss")
    print("=" * 70)

    use_stop = input("\nUtiliser un Stop Loss? (o/n) [o]: ").strip().lower() or "o"

    if use_stop != "o":
        return None

    print("\nType de stop loss:")
    print("  1. Pourcentage fixe (ex: 2%)")
    print("  2. Basé sur ATR (s'adapte à la volatilité)")

    stop_type = input("\nVotre choix (1-2) [1]: ").strip() or "1"

    if stop_type == "1":
        print("\nPourcentage recommandé:")
        print("  • Conservative: 1.5%")
        print("  • Équilibré: 2%")
        print("  • Agressif: 3%")

        stop_input = input("\nPourcentage du Stop Loss (ex: 2 pour 2%) [2]: ").strip()
        stop_pct = float(stop_input) / 100 if stop_input else 0.02

        return {"type": "percentage", "value": stop_pct}
    else:
        print("\nMultiplicateur ATR recommandé:")
        print("  • Serré: 1.5x")
        print("  • Normal: 2x")
        print("  • Large: 3x")

        atr_input = input("\nMultiplicateur ATR [2]: ").strip()
        atr_mult = float(atr_input) if atr_input else 2.0

        return {"type": "atr", "value": atr_mult}


def configure_take_profit():
    """Configure le take profit"""
    print("\n" + "=" * 70)
    print("ÉTAPE 4: Configuration du Take Profit")
    print("=" * 70)

    use_tp = input("\nUtiliser un Take Profit? (o/n) [o]: ").strip().lower() or "o"

    if use_tp != "o":
        return None

    print("\nType de take profit:")
    print("  1. Pourcentage fixe (ex: 5%)")
    print("  2. Ratio Risque/Rendement (ex: 2.5:1)")

    tp_type = input("\nVotre choix (1-2) [2]: ").strip() or "2"

    if tp_type == "1":
        print("\nPourcentage recommandé:")
        print("  • Conservative: 3%")
        print("  • Équilibré: 5%")
        print("  • Agressif: 8%")

        tp_input = input("\nPourcentage (ex: 5 pour 5%) [5]: ").strip()
        tp_pct = float(tp_input) / 100 if tp_input else 0.05

        return {"type": "percentage", "value": tp_pct}
    else:
        print("\nRatio R/R recommandé:")
        print("  • Minimum acceptable: 1.5:1")
        print("  • Recommandé: 2:1 ou 2.5:1")
        print("  • Ambitieux: 3:1 ou plus")

        rr_input = input("\nRatio R/R (ex: 2.5 pour 2.5:1) [2.5]: ").strip()
        rr = float(rr_input) if rr_input else 2.5

        return {"type": "risk_reward", "value": rr}


def configure_trailing_stop():
    """Configure le trailing stop"""
    print("\n" + "=" * 70)
    print("ÉTAPE 5: Configuration du Trailing Stop")
    print("=" * 70)

    print("\nLe trailing stop suit le prix et maximise les profits")
    use_trailing = (
        input("Utiliser un Trailing Stop? (o/n) [o]: ").strip().lower() or "o"
    )

    if use_trailing != "o":
        return None

    print("\nPourcentage de trailing recommandé:")
    print("  • Serré: 2%")
    print("  • Normal: 3%")
    print("  • Large: 5%")

    trail_input = input("\nPourcentage (ex: 3 pour 3%) [3]: ").strip()
    trail_pct = float(trail_input) / 100 if trail_input else 0.03

    print("\nActivation du trailing (gain minimum avant activation):")
    print("  • Rapide: 1.5%")
    print("  • Normal: 2%")
    print("  • Tardif: 3%")

    activation_input = input("\nActivation (ex: 2 pour 2%) [2]: ").strip()
    activation_pct = float(activation_input) / 100 if activation_input else 0.02

    return {"trailing_pct": trail_pct, "activation_pct": activation_pct}


def generate_strategy_code(name, template, stop_loss, take_profit, trailing_stop):
    """Génère le code de la stratégie"""

    # Générer les paramètres de stops
    stop_params = []

    if stop_loss:
        stop_params.append("('use_stop_loss', True),")
        if stop_loss["type"] == "percentage":
            stop_params.append(f"('stop_loss_pct', {stop_loss['value']}),")
        else:
            stop_params.append("('use_atr_stop', True),")
            stop_params.append(f"('stop_loss_atr_mult', {stop_loss['value']}),")
            stop_params.append("('atr_period', 14),")

    if take_profit:
        stop_params.append("('use_take_profit', True),")
        if take_profit["type"] == "percentage":
            stop_params.append(f"('take_profit_pct', {take_profit['value']}),")
        else:
            stop_params.append(f"('risk_reward_ratio', {take_profit['value']}),")

    if trailing_stop:
        stop_params.append("('use_trailing_stop', True),")
        stop_params.append(f"('trailing_stop_pct', {trailing_stop['trailing_pct']}),")
        stop_params.append(
            f"('trailing_activation_pct', {trailing_stop['activation_pct']}),"
        )

    stop_params_str = "\n        ".join(stop_params)

    # Template de base
    code = f'''"""
{name} - Stratégie personnalisée
Créée avec le Strategy Creator interactif
"""

from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt


class {name}(BaseAdvancedStrategy):
    """
    Description de votre stratégie
    
    TODO:
    - Décrire la logique de trading
    - Ajouter les indicateurs nécessaires
    - Implémenter les conditions d'achat/vente
    - Tester et optimiser
    """
    
    params = (
        # Paramètres de la stratégie (à personnaliser)
        ('ma_period', 20),
        ('rsi_period', 14),
        
        # Gestion des risques
        {stop_params_str}
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # ===== AJOUTEZ VOS INDICATEURS ICI =====
        
        # Exemple: Moyenne mobile
        self.ma = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.ma_period
        )
        
        # Exemple: RSI
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        # Autres indicateurs disponibles:
        # self.ema = bt.indicators.EMA(period=20)
        # self.macd = bt.indicators.MACD()
        # self.bollinger = bt.indicators.BollingerBands()
        # self.atr = bt.indicators.ATR(period=14)
        # self.stochastic = bt.indicators.Stochastic()
        
        self.log(f"{name} initialisée avec succès")
    
    def next(self):
        # ===== VÉRIFICATION DES STOPS =====
        # TOUJOURS en premier !
        if self._check_stops():
            return
        
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        # ===== LOGIQUE D'ACHAT =====
        if not self.position:
            
            # TODO: Remplacer par votre logique d'entrée
            # Exemple simple: Prix au-dessus de la MA et RSI < 70
            if current_price > self.ma[0] and self.rsi[0] < 70:
                self.log(f'SIGNAL ACHAT @ {{current_price:.2f}}')
                size = int((self.broker.getcash() * 0.95) / current_price)
                self.order = self.buy(size=size)
        
        # ===== LOGIQUE DE VENTE =====
        else:
            
            # TODO: Remplacer par votre logique de sortie
            # Exemple simple: Prix en-dessous de la MA ou RSI > 70
            if current_price < self.ma[0] or self.rsi[0] > 70:
                self.log(f'SIGNAL VENTE @ {{current_price:.2f}}')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# GUIDE DE PERSONNALISATION
# ═══════════════════════════════════════════════════════════════════════════

"""
PROCHAINES ÉTAPES:

1. Personnaliser les indicateurs:
   - Ajouter/supprimer les indicateurs selon vos besoins
   - Ajuster les périodes

2. Implémenter votre logique de trading:
   - Modifier les conditions d'achat dans "LOGIQUE D'ACHAT"
   - Modifier les conditions de vente dans "LOGIQUE DE VENTE"

3. Tester votre stratégie:
   python main.py --strategy {name} --symbols AAPL

4. Optimiser:
   - Ajuster les paramètres
   - Backtester sur différentes périodes
   - Comparer avec d'autres stratégies

EXEMPLES DE CONDITIONS:

# Croisement de moyennes mobiles
if self.ma_fast[0] > self.ma_slow[0] and self.ma_fast[-1] <= self.ma_slow[-1]:
    # Acheter

# RSI en survente
if self.rsi[0] < 30:
    # Acheter

# Prix sort des bandes de Bollinger
if current_price < self.bollinger.lines.bot[0]:
    # Acheter

# Breakout
if current_price > self.highest_20days[0]:
    # Acheter

# Combinaison multiple
if (trend_up and rsi_oversold and high_volume):
    # Acheter

RESSOURCES:

- Backtrader Indicators: https://www.backtrader.com/docu/indautoref/
- Documentation complète: README.md
- Templates: strategies/strategy_templates.py
"""
'''

    return code


def save_strategy(name, code):
    """Sauvegarde la stratégie"""
    filename = f"strategies/{name.lower()}.py"
    filepath = Path(filename)

    # Créer le dossier si nécessaire
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)

    return filename


def print_next_steps(name, filename):
    """Affiche les prochaines étapes"""
    print("\n" + "=" * 70)
    print("✅ STRATÉGIE CRÉÉE AVEC SUCCÈS !")
    print("=" * 70)

    print(f"\n📄 Fichier créé: {filename}")

    print("\n📝 Prochaines étapes:\n")
    print(f"  1. Éditer votre stratégie:")
    print(f"     nano {filename}")
    print(f"     # ou votre éditeur préféré\n")

    print(f"  2. Personnaliser les indicateurs et la logique\n")

    print(f"  3. Tester votre stratégie:")
    print(f"     python main.py --strategy {name} --symbols AAPL\n")

    print(f"  4. Avec graphiques:")
    print(f"     python main.py --strategy {name} --symbols AAPL --plot\n")

    print(f"  5. Mode verbose pour debug:")
    print(f"     python main.py --strategy {name} --symbols AAPL --verbose\n")

    print("=" * 70)
    print("\n💡 Conseil: Commencez par de petites modifications")
    print("   et testez après chaque changement !\n")
    print("🎯 Bonne création et bon trading ! 🚀\n")


def create_strategy_interactive():
    """Fonction principale"""

    try:
        print_banner()

        # Étape 1: Choisir le template
        template = choose_template()
        print(f"\n✓ Template sélectionné: {template}")

        # Étape 2: Nom de la stratégie
        name = get_strategy_name()
        print(f"\n✓ Nom de la stratégie: {name}")

        # Étape 3: Stop loss
        stop_loss = configure_stop_loss()
        if stop_loss:
            if stop_loss["type"] == "percentage":
                print(f"\n✓ Stop Loss: {stop_loss['value']*100}%")
            else:
                print(f"\n✓ Stop Loss: {stop_loss['value']}x ATR")
        else:
            print("\n✓ Pas de Stop Loss")

        # Étape 4: Take profit
        take_profit = configure_take_profit()
        if take_profit:
            if take_profit["type"] == "percentage":
                print(f"\n✓ Take Profit: {take_profit['value']*100}%")
            else:
                print(f"\n✓ Take Profit: R/R {take_profit['value']}:1")
        else:
            print("\n✓ Pas de Take Profit")

        # Étape 5: Trailing stop
        trailing_stop = configure_trailing_stop()
        if trailing_stop:
            print(
                f"\n✓ Trailing Stop: {trailing_stop['trailing_pct']*100}% "
                f"(activation à {trailing_stop['activation_pct']*100}%)"
            )
        else:
            print("\n✓ Pas de Trailing Stop")

        # Générer le code
        print("\n" + "=" * 70)
        print("Génération du code...")
        code = generate_strategy_code(
            name, template, stop_loss, take_profit, trailing_stop
        )

        # Sauvegarder
        filename = save_strategy(name, code)

        # Afficher les prochaines étapes
        print_next_steps(name, filename)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Création annulée par l'utilisateur")
        return 1

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = create_strategy_interactive()
    sys.exit(exit_code)
