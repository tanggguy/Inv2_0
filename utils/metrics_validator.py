#!/usr/bin/env python3
"""
Validateur et correcteur de métriques
=====================================

Module pour valider et corriger les métriques de backtest afin d'éviter
les valeurs aberrantes causées par des divisions par zéro ou des overflows.

Usage:
    from metrics_validator import MetricsValidator
    
    validator = MetricsValidator()
    clean_metrics = validator.validate_and_clean(raw_metrics)
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MetricsValidator:
    """
    Validateur et correcteur de métriques de trading
    
    Gère:
    - Détection de valeurs aberrantes
    - Correction des calculs de return/drawdown
    - Protection contre division par zéro
    - Normalisation des métriques
    """
    
    # Seuils de validation
    MAX_RETURN_PCT = 10000  # 10,000% maximum raisonnable
    MIN_RETURN_PCT = -100   # -100% minimum (perte totale)
    MAX_DRAWDOWN_PCT = 100  # 100% maximum (perte totale)
    MIN_TRADES = 0
    MAX_TRADES = 100000
    MIN_CAPITAL = 0.01
    
    def __init__(self, verbose: bool = False):
        """
        Initialise le validateur
        
        Args:
            verbose: Activer les logs détaillés
        """
        self.verbose = verbose
        self.validation_issues = []
    
    def validate_and_clean(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et nettoie les métriques
        
        Args:
            metrics: Dictionnaire de métriques brutes
        
        Returns:
            Dictionnaire de métriques nettoyées
        """
        self.validation_issues = []
        clean_metrics = metrics.copy()
        
        # 1. Valider les valeurs de portefeuille
        clean_metrics = self._validate_portfolio_values(clean_metrics)
        
        # 2. Recalculer le return de manière sécurisée
        clean_metrics = self._recalculate_return(clean_metrics)
        
        # 3. Valider le drawdown
        clean_metrics = self._validate_drawdown(clean_metrics)
        
        # 4. Valider les trades
        clean_metrics = self._validate_trades(clean_metrics)
        
        # 5. Valider le Sharpe ratio
        clean_metrics = self._validate_sharpe(clean_metrics)
        
        # Log des problèmes détectés
        if self.validation_issues and self.verbose:
            logger.warning("⚠️ Problèmes détectés dans les métriques:")
            for issue in self.validation_issues:
                logger.warning(f"  - {issue}")
        
        return clean_metrics
    
    def _validate_portfolio_values(self, metrics: Dict) -> Dict:
        """
        Valide les valeurs initiale et finale du portefeuille
        
        Args:
            metrics: Métriques à valider
        
        Returns:
            Métriques corrigées
        """
        initial = metrics.get('initial_value', 0)
        final = metrics.get('final_value', 0)
        
        # Vérifier que les valeurs sont positives et raisonnables
        if initial <= self.MIN_CAPITAL:
            self.validation_issues.append(
                f"Valeur initiale invalide: {initial} (devrait être > {self.MIN_CAPITAL})"
            )
            # Utiliser une valeur par défaut
            metrics['initial_value'] = metrics.get('capital', 100000)
            if self.verbose:
                logger.warning(f"Correction: initial_value = {metrics['initial_value']}")
        
        if final < 0:
            self.validation_issues.append(
                f"Valeur finale négative: {final}"
            )
            # Le minimum est 0 (perte totale)
            metrics['final_value'] = 0
        
        return metrics
    
    def _recalculate_return(self, metrics: Dict) -> Dict:
        """
        Recalcule le return de manière sécurisée
        
        Args:
            metrics: Métriques à recalculer
        
        Returns:
            Métriques avec return corrigé
        """
        initial = metrics.get('initial_value', 0)
        final = metrics.get('final_value', 0)
        
        # Protection contre division par zéro
        if initial <= 0:
            self.validation_issues.append(
                "Division par zéro évitée dans le calcul du return"
            )
            metrics['total_return'] = 0.0
            return metrics
        
        # Calcul sécurisé
        try:
            return_pct = ((final - initial) / initial) * 100
            
            # Vérifier que la valeur est dans des limites raisonnables
            if not np.isfinite(return_pct):
                self.validation_issues.append(
                    f"Return non-fini détecté: {return_pct}"
                )
                return_pct = 0.0
            
            # Limiter aux seuils
            if return_pct > self.MAX_RETURN_PCT:
                self.validation_issues.append(
                    f"Return aberrant détecté: {return_pct:.2f}% > {self.MAX_RETURN_PCT}%"
                )
                return_pct = self.MAX_RETURN_PCT
            
            if return_pct < self.MIN_RETURN_PCT:
                self.validation_issues.append(
                    f"Return aberrant détecté: {return_pct:.2f}% < {self.MIN_RETURN_PCT}%"
                )
                return_pct = self.MIN_RETURN_PCT
            
            metrics['total_return'] = round(return_pct, 2)
            
        except (ZeroDivisionError, OverflowError, ValueError) as e:
            self.validation_issues.append(
                f"Erreur dans le calcul du return: {e}"
            )
            metrics['total_return'] = 0.0
        
        return metrics
    
    def _validate_drawdown(self, metrics: Dict) -> Dict:
        """
        Valide le drawdown
        
        Args:
            metrics: Métriques à valider
        
        Returns:
            Métriques avec drawdown corrigé
        """
        drawdown = metrics.get('max_drawdown', 0)
        
        # Le drawdown devrait être négatif ou 0
        drawdown = abs(drawdown)
        
        if not np.isfinite(drawdown):
            self.validation_issues.append(
                f"Drawdown non-fini détecté: {drawdown}"
            )
            drawdown = 0.0
        
        # Limiter à 100% maximum (perte totale)
        if drawdown > self.MAX_DRAWDOWN_PCT:
            self.validation_issues.append(
                f"Drawdown aberrant détecté: {drawdown:.2f}% > {self.MAX_DRAWDOWN_PCT}%"
            )
            drawdown = self.MAX_DRAWDOWN_PCT
        
        metrics['max_drawdown'] = round(drawdown, 2)
        
        return metrics
    
    def _validate_trades(self, metrics: Dict) -> Dict:
        """
        Valide les statistiques de trades
        
        Args:
            metrics: Métriques à valider
        
        Returns:
            Métriques avec trades corrigés
        """
        total_trades = metrics.get('total_trades', 0)
        won_trades = metrics.get('won_trades', 0)
        lost_trades = metrics.get('lost_trades', 0)
        
        # Vérifier cohérence
        if won_trades + lost_trades != total_trades:
            self.validation_issues.append(
                f"Incohérence dans les trades: {won_trades} + {lost_trades} != {total_trades}"
            )
        
        # Recalculer le win rate
        if total_trades > 0:
            win_rate = (won_trades / total_trades) * 100
            metrics['win_rate'] = round(win_rate, 2)
        else:
            metrics['win_rate'] = 0.0
        
        return metrics
    
    def _validate_sharpe(self, metrics: Dict) -> Dict:
        """
        Valide le Sharpe ratio
        
        Args:
            metrics: Métriques à valider
        
        Returns:
            Métriques avec Sharpe corrigé
        """
        sharpe = metrics.get('sharpe_ratio', 0)
        
        # Vérifier que c'est un nombre fini
        if not np.isfinite(sharpe):
            self.validation_issues.append(
                f"Sharpe ratio non-fini détecté: {sharpe}"
            )
            sharpe = 0.0
        
        # Les Sharpe ratios très élevés sont suspects
        if abs(sharpe) > 10:
            self.validation_issues.append(
                f"Sharpe ratio suspect: {sharpe:.2f} (|sharpe| > 10)"
            )
        
        metrics['sharpe_ratio'] = round(sharpe, 4)
        
        return metrics
    
    def is_valid_backtest(self, metrics: Dict) -> bool:
        """
        Vérifie si un backtest est valide
        
        Critères:
        - Au moins 5 trades
        - Return dans des limites raisonnables
        - Pas de valeurs non-finies
        
        Args:
            metrics: Métriques à vérifier
        
        Returns:
            True si le backtest est valide
        """
        # Nettoyer d'abord
        clean_metrics = self.validate_and_clean(metrics)
        
        # Critères de validation
        checks = [
            clean_metrics.get('total_trades', 0) >= 5,
            np.isfinite(clean_metrics.get('total_return', 0)),
            np.isfinite(clean_metrics.get('sharpe_ratio', 0)),
            clean_metrics.get('initial_value', 0) > self.MIN_CAPITAL,
        ]
        
        return all(checks)
    
    def get_validation_report(self) -> str:
        """
        Génère un rapport des problèmes de validation
        
        Returns:
            Rapport texte
        """
        if not self.validation_issues:
            return "✅ Aucun problème de validation détecté"
        
        report = "⚠️ Problèmes de validation détectés:\n"
        for i, issue in enumerate(self.validation_issues, 1):
            report += f"{i}. {issue}\n"
        
        return report


def safe_calculate_return(initial_value: float, final_value: float) -> float:
    """
    Calcule le return de manière sécurisée
    
    Args:
        initial_value: Valeur initiale du portefeuille
        final_value: Valeur finale du portefeuille
    
    Returns:
        Return en pourcentage
    """
    if initial_value <= 0:
        logger.warning(f"⚠️ Initial value invalide: {initial_value}")
        return 0.0
    
    try:
        return_pct = ((final_value - initial_value) / initial_value) * 100
        
        # Vérifier que c'est un nombre fini
        if not np.isfinite(return_pct):
            logger.warning(f"⚠️ Return non-fini: {return_pct}")
            return 0.0
        
        # Limiter aux valeurs raisonnables
        return_pct = max(min(return_pct, 10000), -100)
        
        return round(return_pct, 2)
        
    except Exception as e:
        logger.error(f"❌ Erreur calcul return: {e}")
        return 0.0


# Exemple d'utilisation
if __name__ == "__main__":
    # Métriques avec des problèmes
    problematic_metrics = {
        'initial_value': 0.0001,  # Presque zéro
        'final_value': 150000,
        'total_return': 1.5e+100,  # Valeur aberrante
        'max_drawdown': -99999,
        'total_trades': 2,
        'won_trades': 1,
        'lost_trades': 1,
        'sharpe_ratio': 0.5774
    }
    
    # Valider et nettoyer
    validator = MetricsValidator(verbose=True)
    clean = validator.validate_and_clean(problematic_metrics)
    
    print("\n" + "="*60)
    print("MÉTRIQUES NETTOYÉES")
    print("="*60)
    for key, value in clean.items():
        print(f"{key}: {value}")
    
    print("\n" + validator.get_validation_report())