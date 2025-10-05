#!/usr/bin/env python3
"""
Optimiseur unifié pour les stratégies de trading

Consolide Grid Search, Walk-Forward et autres méthodes d'optimisation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backtrader as bt
import pandas as pd
from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Callable

from config import settings
from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger
from optimization.optimization_config import OptimizationConfig
from optimization.results_storage import ResultsStorage

logger = setup_logger("optimizer")


class UnifiedOptimizer:
    """
    Optimiseur unifié supportant plusieurs méthodes d'optimisation
    
    Méthodes supportées:
    - Grid Search: Test exhaustif de toutes les combinaisons
    - Walk-Forward: Validation robuste contre l'overfitting
    - Random Search: Échantillonnage aléatoire (futur)
    """
    
    def __init__(self, 
                 strategy_class,
                 config: Dict,
                 optimization_type: str = "grid_search",
                 verbose: bool = True):
        """
        Initialise l'optimiseur
        
        Args:
            strategy_class: Classe de la stratégie à optimiser
            config: Configuration (peut être un preset ou custom)
            optimization_type: 'grid_search', 'walk_forward', 'random_search'
            verbose: Afficher les logs détaillés
        """
        self.strategy_class = strategy_class
        self.config = config
        self.optimization_type = optimization_type
        self.verbose = verbose
        
        # Valider la config
        config_manager = OptimizationConfig()
        is_valid, errors = config_manager.validate_config(config)
        if not is_valid:
            raise ValueError(f"Configuration invalide: {', '.join(errors)}")
            
        config_manager = OptimizationConfig()
        is_params_valid, param_warnings = config_manager.validate_strategy_params(
            strategy_class,
            config.get('param_grid', {})
            )
        if param_warnings:
            logger.warning("⚠️  Avertissements de paramètres:")
        for warning in param_warnings:
            logger.warning(f"  {warning}")
        # Extraire les infos
        self.strategy_name = strategy_class.__name__
        self.symbols = config['symbols']
        self.start_date = config['period']['start']
        self.end_date = config['period']['end']
        self.capital = config.get('capital', 100000)
        self.param_grid = config['param_grid']
        
        # Walk-forward config (si applicable)
        self.walk_forward_config = config.get('walk_forward', {})
        
        # Génération du run ID
        self.storage = ResultsStorage()
        self.run_id = self.storage.generate_run_id(self.strategy_name, optimization_type)
        self.storage = ResultsStorage()
        self.run_id = self.storage.generate_run_id(self.strategy_name, optimization_type)
        
        # AJOUTEZ CES LIGNES ICI:
        self.verbose = verbose
        
        # Data handler
        self.data_handler = DataHandler()
        
        # Résultats
        self.results = []
        self.best_result = None
        
        logger.info(f"🔬 UnifiedOptimizer initialisé: {self.strategy_name}")
        logger.info(f"   Type: {optimization_type}")
        logger.info(f"   Run ID: {self.run_id}")


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

        
        # Data handler
        self.data_handler = DataHandler()
        
        # Résultats
        self.results = []
        self.best_result = None
        
        logger.info(f"🔬 UnifiedOptimizer initialisé: {self.strategy_name}")
        logger.info(f"   Type: {optimization_type}")
        logger.info(f"   Run ID: {self.run_id}")
    
    def run(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Lance l'optimisation selon le type choisi
        
        Args:
            progress_callback: Fonction callback pour progression (optionnel)
        
        Returns:
            Dict avec résultats
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 DÉMARRAGE OPTIMISATION: {self.optimization_type.upper()}")
        logger.info(f"{'='*80}")
        
        if self.optimization_type == "grid_search":
            return self._grid_search(progress_callback)
        elif self.optimization_type == "walk_forward":
            return self._walk_forward(progress_callback)
        elif self.optimization_type == "random_search":
            return self._random_search(progress_callback)
        else:
            raise ValueError(f"Type d'optimisation non supporté: {self.optimization_type}")
    
    def _grid_search(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Grid Search: teste toutes les combinaisons de paramètres
        
        Args:
            progress_callback: Fonction callback(progress_pct)
        
        Returns:
            Dict avec résultats
        """
        # Générer toutes les combinaisons
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        logger.info(f"📊 Grid Search: {total} combinaisons à tester")
        logger.info(f"   Symboles: {', '.join(self.symbols)}")
        logger.info(f"   Période: {self.start_date} → {self.end_date}")
        logger.info(f"   Paramètres: {self.param_grid}\n")
        
        # Tester chaque combinaison
        for i, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))
            
            if self.verbose:
                logger.info(f"[{i}/{total}] Test: {params}")
            
            # Exécuter le backtest
            result = self._run_single_backtest(params)
            
            if result:
                self.results.append(result)
                
                if self.verbose:
                    logger.info(f"   → Sharpe: {result['sharpe']:.2f}, Return: {result['return']:.2f}%")
            
            # Callback progression
            if progress_callback:
                progress_callback(i / total)
        
        # Analyser les résultats
        return self._analyze_results()
    
    def _walk_forward(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Walk-Forward Optimization: validation robuste contre l'overfitting
        
        Args:
            progress_callback: Fonction callback(progress_pct)
        
        Returns:
            Dict avec résultats
        """
        in_sample_months = self.walk_forward_config.get('in_sample_months', 12)
        out_sample_months = self.walk_forward_config.get('out_sample_months', 12)
        
        logger.info(f"Walk-Forward Optimization")
        logger.info(f"   In-Sample: {in_sample_months} mois")
        logger.info(f"   Out-Sample: {out_sample_months} mois\n")
        
        # Générer les périodes
        periods = self._generate_walk_forward_periods(in_sample_months, out_sample_months)
        
        logger.info(f"   Périodes générées: {len(periods)}\n")
        
        walk_forward_results = []
        total_steps = len(periods)
        
        for i, period in enumerate(periods, 1):
            logger.info(f"{'='*80}")
            logger.info(f"PÉRIODE {i}/{total_steps}")
            logger.info(f"{'='*80}")
            
            in_start, in_end = period['in_sample']
            out_start, out_end = period['out_sample']
            
            logger.info(f"📊 In-Sample:  {in_start} → {in_end}")
            logger.info(f"📈 Out-Sample: {out_start} → {out_end}\n")
            
            # 1. Optimiser sur In-Sample
            logger.info("🔬 Optimisation sur In-Sample...")
            
            # Créer optimiseur temporaire pour In-Sample
            in_sample_config = self.config.copy()
            in_sample_config['period'] = {'start': in_start, 'end': in_end}
            
            in_sample_optimizer = UnifiedOptimizer(
                self.strategy_class,
                in_sample_config,
                optimization_type='grid_search',
                verbose=False
            )
            
            in_sample_results = in_sample_optimizer._grid_search()
            
            if not in_sample_results or 'best' not in in_sample_results:
                logger.warning(f"Période {i}: Pas de résultats In-Sample")
                continue
            
            best_params = {k: v for k, v in in_sample_results['best'].items() 
                          if k not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']}
            
            in_sharpe = in_sample_results['best'].get('sharpe', 0) or 0
            in_return = in_sample_results['best'].get('return', 0) or 0
            
            logger.info(f"✓ Meilleurs paramètres In-Sample: {best_params}")
            logger.info(f"  Sharpe: {in_sharpe:.2f}, Return: {in_return:.2f}%\n")
            
            # 2. Tester sur Out-Sample avec ces paramètres
            logger.info("🧪 Test sur Out-Sample...")
            
            out_result = self._run_single_backtest(
                best_params,
                start_date=out_start,
                end_date=out_end
            )
            
            if out_result and out_result.get('trades', 0) > 0:
                out_sharpe = out_result.get('sharpe', 0) or 0
                out_return = out_result.get('return', 0) or 0
                
                logger.info(f"✓ Résultats Out-Sample:")
                logger.info(f"  Sharpe: {out_sharpe:.2f}, Return: {out_return:.2f}%")
                logger.info(f"  Trades: {out_result.get('trades', 0)}\n")
                
                degradation = in_sharpe - out_sharpe
                
                walk_forward_results.append({
                    'period': i,
                    'in_sample': {'start': in_start, 'end': in_end},
                    'out_sample': {'start': out_start, 'end': out_end},
                    'best_params': best_params,
                    'in_sharpe': in_sharpe,
                    'in_return': in_return,
                    'out_sharpe': out_sharpe,
                    'out_return': out_return,
                    'out_trades': out_result.get('trades', 0),
                    'degradation': degradation
                })
            else:
                logger.warning(f"Période {i}: Aucun trade en Out-Sample\n")
            
            # Callback progression
            if progress_callback:
                progress_callback(i / total_steps)
        
        # Analyser les résultats Walk-Forward
        return self._analyze_walk_forward_results(walk_forward_results)
    
    def _random_search(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Random Search: échantillonnage aléatoire (à implémenter)
        """
        logger.warning("Random Search pas encore implémenté")
        return {}
    
    def _run_single_backtest(self, 
                            params: Dict,
                            start_date: str = None,
                            end_date: str = None) -> Optional[Dict]:
        """
        Exécute un seul backtest avec des paramètres donnés
        
        Args:
            params: Paramètres de la stratégie
            start_date: Date de début (override)
            end_date: Date de fin (override)
        
        Returns:
            Dict avec résultats ou None
        """
        try:
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(self.capital)
            cerebro.broker.setcommission(commission=settings.COMMISSION)
            
            # Charger les données
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            for symbol in self.symbols:
                df = self.data_handler.fetch_data(symbol, start, end)
                if df is not None and not df.empty:
                    data_feed = create_data_feed(df, name=symbol)
                    cerebro.adddata(data_feed, name=symbol)
            
            # Ajouter la stratégie avec paramètres
            # Convertir les paramètres (float → int si nécessaire)
            converted_params = self._convert_params(params)
            cerebro.addstrategy(self.strategy_class, **converted_params, printlog=False)
            
            # Analyseurs
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            # Exécuter
            start_value = cerebro.broker.getvalue()
            strategies = cerebro.run()
            end_value = cerebro.broker.getvalue()
            
            # Récupérer les résultats
            strat = strategies[0]
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            
            result = {
                **params,  # Inclure les paramètres
                'sharpe': sharpe.get('sharperatio', 0) or 0,
                'return': ((end_value - start_value) / start_value) * 100,
                'drawdown': drawdown.get('max', {}).get('drawdown', 0),
                'trades': total_trades,
                'win_rate': (won_trades / total_trades * 100) if total_trades > 0 else 0
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur backtest: {e}")
            return None
    
    def _generate_walk_forward_periods(self, in_sample_months: int, out_sample_months: int) -> List[Dict]:
        """Génère les périodes pour Walk-Forward"""
        periods = []
        start_date = pd.to_datetime(self.start_date)
        end_date = pd.to_datetime(self.end_date)
        
        current_date = start_date
        
        while current_date + relativedelta(months=in_sample_months + out_sample_months) <= end_date:
            in_start = current_date
            in_end = current_date + relativedelta(months=in_sample_months)
            out_start = in_end
            out_end = out_start + relativedelta(months=out_sample_months)
            
            periods.append({
                'in_sample': (in_start.strftime('%Y-%m-%d'), in_end.strftime('%Y-%m-%d')),
                'out_sample': (out_start.strftime('%Y-%m-%d'), out_end.strftime('%Y-%m-%d'))
            })
            
            current_date = out_start
        
        return periods
    
    def _analyze_results(self) -> Dict:
        """Analyse les résultats du Grid Search"""
        if not self.results:
            logger.error("❌ Aucun résultat disponible")
            return {'run_id': self.run_id, 'best': {}, 'all_results': []}
        
        # Convertir en DataFrame
        df = pd.DataFrame(self.results)
        
        # Trier par Sharpe Ratio
        df_sorted = df.sort_values('sharpe', ascending=False)
        
        # Meilleur résultat
        self.best_result = df_sorted.iloc[0].to_dict()
        
        logger.info(f"\n{'='*80}")
        logger.info("🏆 MEILLEURE COMBINAISON")
        logger.info(f"{'='*80}")
        for key, value in self.best_result.items():
            if key in ['sharpe', 'return', 'drawdown', 'win_rate']:
                logger.info(f"{key:.<30} {value:.2f}")
            else:
                logger.info(f"{key:.<30} {value}")
        
        results_dict = {
            'run_id': self.run_id,
            'best': self.best_result,
            'all_results': self.results,
            'total_combinations': len(self.results)
        }
        
        # Sauvegarder
        self._save_results(results_dict)
        
        return results_dict
    
    def _analyze_walk_forward_results(self, wf_results: List[Dict]) -> Dict:
        """Analyse les résultats du Walk-Forward"""
        if not wf_results:
            logger.error("❌ Aucun résultat Walk-Forward valide")
            return {'run_id': self.run_id, 'best': {}, 'all_results': []}
        
        df = pd.DataFrame(wf_results)
        
        logger.info(f"\n{'='*80}")
        logger.info("📊 ANALYSE WALK-FORWARD")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n🎯 PERFORMANCE MOYENNE:")
        logger.info(f"   In-Sample Sharpe:   {df['in_sharpe'].mean():.2f} (±{df['in_sharpe'].std():.2f})")
        logger.info(f"   Out-Sample Sharpe:  {df['out_sharpe'].mean():.2f} (±{df['out_sharpe'].std():.2f})")
        logger.info(f"   Dégradation moyenne: {df['degradation'].mean():.2f}")
        
        avg_degradation = df['degradation'].mean()
        if avg_degradation < 0.3:
            logger.info("   ✅ EXCELLENT - Stratégie robuste")
        elif avg_degradation < 0.5:
            logger.info("   ✓ BON - Dégradation acceptable")
        else:
            logger.info("   ⚠️  ATTENTION - Overfitting détecté")
        
        # Meilleur résultat basé sur Out-Sample
        best_period = df.loc[df['out_sharpe'].idxmax()]
        
        results_dict = {
            'run_id': self.run_id,
            'best': best_period.to_dict(),
            'all_results': wf_results,
            'statistics': {
                'avg_in_sharpe': float(df['in_sharpe'].mean()),
                'avg_out_sharpe': float(df['out_sharpe'].mean()),
                'avg_degradation': float(df['degradation'].mean())
            }
        }
        
        # Sauvegarder
        self._save_results(results_dict)
        
        return results_dict
    
    def _save_results(self, results: Dict):
        """Sauvegarde les résultats"""
        # Préparer la config complète pour sauvegarde
        full_config = {
            **self.config,
            'strategy_name': self.strategy_name,
            'optimization_type': self.optimization_type
        }
        
        # Sauvegarder
        self.storage.save_run(
            run_id=self.run_id,
            config=full_config,
            results=results,
            optimization_type=self.optimization_type
        )
        
        logger.info(f"\n✅ Résultats sauvegardés: {self.run_id}")
    
    def get_best_params(self) -> Dict:
        """Retourne les meilleurs paramètres trouvés"""
        if not self.best_result:
            return {}
        
        # Filtrer pour ne garder que les paramètres (pas les métriques)
        return {k: v for k, v in self.best_result.items() 
                if k not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']}


# Fonctions helper pour usage simple
def optimize(strategy_class, 
            preset_name: str = "standard",
            optimization_type: str = "grid_search") -> Dict:
    """
    Fonction helper pour optimiser rapidement avec un preset
    
    Args:
        strategy_class: Classe de stratégie
        preset_name: Nom du preset
        optimization_type: Type d'optimisation
    
    Returns:
        Résultats de l'optimisation
    """
    from optimization.optimization_config import load_preset
    
    config = load_preset(preset_name)
    optimizer = UnifiedOptimizer(strategy_class, config, optimization_type)
    return optimizer.run()


if __name__ == "__main__":
    # Test avec MaSuperStrategie
    print("="*80)
    print("TEST UNIFIED OPTIMIZER")
    print("="*80)
    
    from strategies.masuperstrategie import MaSuperStrategie
    from optimization.optimization_config import load_preset
    
    # Test Grid Search
    print("\n🔬 Test Grid Search avec preset 'quick':\n")
    config = load_preset('quick')
    
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='grid_search'
    )
    
    results = optimizer.run()
    
    print("\n✓ Optimisation terminée !")
    print(f"Run ID: {results['run_id']}")
    print(f"Meilleur Sharpe: {results['best'].get('sharpe', 0):.2f}")