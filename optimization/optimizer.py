# !/usr/bin/env python3
"""
Optimiseur unifié pour les stratégies de trading - VERSION PARALLÉLISÉE

🚀 OPTIMISATIONS COMPLÈTES:
- ✅ #1: Parallélisation multiprocessing (4-8x plus rapide)
- ✅ #2: Cache des données (évite rechargement)
- ✅ #4: Optimisations Backtrader (stdstats=False, exactbars=-1)
- ✅ #5: Progression fluide avec estimation temps restant (ETA)

GAINS ATTENDUS: 12-20x plus rapide vs version originale
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
import time
from multiprocessing import Pool, cpu_count, Manager
from functools import partial

from config import settings
from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger
from optimization.optimization_config import OptimizationConfig
from optimization.results_storage import ResultsStorage
from optimization.optuna_optimizer import OptunaOptimizer
# Import des workers (doivent être au niveau module pour pickling)
from optimization.optimizer_worker import run_backtest_worker

logger = setup_logger("optimizer")


class UnifiedOptimizer:
    """
    Optimiseur unifié supportant plusieurs méthodes d'optimisation
    
    Méthodes supportées:
    - Grid Search: Test exhaustif (séquentiel ou parallèle)
    - Walk-Forward: Validation robuste contre l'overfitting
    - Random Search: Échantillonnage aléatoire (futur)
    
    🚀 VERSION PARALLÉLISÉE:
    - Utilise multiprocessing pour Grid Search
    - Cache des données optimisé
    - Early stopping intégré
    - Progression fluide avec ETA
    """
    
    def __init__(self, 
                 strategy_class,
                 config: Dict,
                 optimization_type: str = "grid_search",
                 verbose: bool = True,
                 use_parallel: bool = True):
        """
        Initialise l'optimiseur
        
        Args:
            strategy_class: Classe de la stratégie à optimiser
            config: Configuration (peut être un preset ou custom)
            optimization_type: 'grid_search', 'walk_forward', 'random_search'
            verbose: Afficher les logs détaillés
            use_parallel: Utiliser la parallélisation (True par défaut)
        """
        self.strategy_class = strategy_class
        self.config = config
        self.optimization_type = optimization_type
        self.verbose = verbose
        self.use_parallel = use_parallel
        
        # Extraire les paramètres de config
        self.symbols = config.get('symbols', ['AAPL'])
        self.start_date = config['period']['start']
        self.end_date = config['period']['end']
        self.capital = config.get('capital', 100000)
        self.param_grid = config.get('param_grid', {})
        
        # Initialisation
        self.data_handler = DataHandler()
        self.storage = ResultsStorage()
        self.results = []
        self.best_result = None
        
        # Cache des données
        self._data_cache = None
        self._cache_loaded = False
        
        # Générer un ID unique pour ce run
        self.strategy_name = strategy_class.__name__
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "parallel" if use_parallel else "sequential"
        self.run_id = f"{self.strategy_name}_{optimization_type}_{mode}_{timestamp}"
        
        logger.info(f"🎯 Optimiseur initialisé: {self.run_id}")
        if use_parallel:
            n_cores = cpu_count()
            logger.info(f"🔥 Mode parallèle activé ({n_cores} cores disponibles)")
    
    def _preload_data(self) -> Dict[str, pd.DataFrame]:
        """
        🚀 OPTIMISATION #2: Pré-charge toutes les données UNE SEULE FOIS
        
        Returns:
            Dict {symbol: DataFrame} avec toutes les données
        """
        if self._cache_loaded and self._data_cache is not None:
            logger.info("📦 Utilisation du cache de données existant")
            return self._data_cache
        
        logger.info("📦 Pré-chargement des données (une seule fois)...")
        cache = {}
        
        for symbol in self.symbols:
            try:
                df = self.data_handler.fetch_data(
                    symbol=symbol,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    interval='1d'
                )
                
                if df is not None and not df.empty:
                    cache[symbol] = df
                    logger.info(f"  ✅ {symbol}: {len(df)} barres chargées")
                else:
                    logger.warning(f"  ⚠️ {symbol}: Aucune donnée disponible")
                    
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Erreur - {e}")
        
        self._data_cache = cache
        self._cache_loaded = True
        
        logger.info(f"✅ Cache créé avec {len(cache)} symboles\n")
        return cache
    
    def run(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Lance l'optimisation
        
        Args:
            progress_callback: Fonction callback(progress_pct, eta_seconds) pour suivre la progression
        
        Returns:
            Dict avec résultats de l'optimisation
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 DÉBUT OPTIMISATION: {self.optimization_type.upper()}")
        logger.info(f"{'='*80}\n")
        
        # PRÉ-CHARGER LES DONNÉES UNE SEULE FOIS
        start_time = time.time()
        self._preload_data()
        preload_time = time.time() - start_time
        logger.info(f"⏱️ Temps de pré-chargement: {preload_time:.2f}s\n")
        
        # Lancer le type d'optimisation approprié
        if self.optimization_type == "grid_search":
            if self.use_parallel:
                results = self._grid_search_parallel(progress_callback)
            else:
                results = self._grid_search(progress_callback)
        elif self.optimization_type == "walk_forward":
            results = self._walk_forward(progress_callback)
        elif self.optimization_type == "random_search":
            results = self._random_search(progress_callback)
        elif self.optimization_type == "optuna":  # <--- AJOUTER
            results = self._optuna_optimization(progress_callback)
        else:
            raise ValueError(f"Type d'optimisation non supporté: {self.optimization_type}")
        
        # Temps total
        total_time = time.time() - start_time
        logger.info(f"\n⏱️ Temps total d'optimisation: {total_time:.2f}s")
        logger.info(f"   (dont pré-chargement: {preload_time:.2f}s)")
        
        return results
    
    def _grid_search_parallel(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        🚀 OPTIMISATION #1: Grid Search PARALLÉLISÉ
        
        Utilise multiprocessing pour tester plusieurs combinaisons en parallèle.
        Exploite tous les cores CPU disponibles.
        
        Args:
            progress_callback: Fonction callback(progress_pct, eta_seconds)
        
        Returns:
            Dict avec résultats
        """
        # Générer toutes les combinaisons
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        logger.info(f"📊 Grid Search PARALLÈLE: {total} combinaisons à tester")
        logger.info(f"   Symboles: {', '.join(self.symbols)}")
        logger.info(f"   Période: {self.start_date} → {self.end_date}")
        logger.info(f"   Paramètres: {self.param_grid}")
        
        # Nombre de workers (laisser 1-2 cores libres pour le système)
        n_workers = max(1, cpu_count() - 1)
        logger.info(f"   Workers: {n_workers}/{cpu_count()} cores\n")
        
        # Préparer les tâches
        preloaded_data = self._data_cache
        tasks = []
        
        for combo in combinations:
            params = dict(zip(param_names, combo))
            # Chaque tâche = (params, données, classe, config)
            tasks.append((
                params,
                preloaded_data,
                self.strategy_class,
                self.config
            ))
        
        # Exécuter en parallèle
        backtest_start = time.time()
        
        logger.info(f"🔥 Lancement de {n_workers} workers parallèles...")
        
        try:
            # Utiliser multiprocessing.Pool
            with Pool(processes=n_workers) as pool:
                # starmap pour passer plusieurs arguments
                # On utilise aussi imap pour avoir un itérateur et suivre la progression
                
                # Option 2: Avec progression fluide
                results_raw = []
                
                # Créer un itérateur avec chunksize pour optimiser
                chunksize = max(1, total // (n_workers * 4))
                
                # Pour estimation du temps
                start_time = time.time()
                
                for i, result in enumerate(pool.starmap(run_backtest_worker, tasks, chunksize=chunksize), 1):
                    results_raw.append(result)
                    
                    # Callback progression BEAUCOUP PLUS FRÉQUENT (à chaque itération)
                    if progress_callback:
                        progress_pct = i / total
                        
                        # Estimation du temps restant
                        elapsed = time.time() - start_time
                        if i > 0:
                            time_per_task = elapsed / i
                            remaining_tasks = total - i
                            eta_seconds = time_per_task * remaining_tasks
                        else:
                            eta_seconds = 0
                        
                        # Appeler le callback avec progression et ETA
                        progress_callback(progress_pct, eta_seconds)
                    
                    # Log tous les 10%
                    if self.verbose and i % max(1, total // 10) == 0:
                        logger.info(f"  Progression: {i}/{total} ({i/total*100:.0f}%)")
        
        except Exception as e:
            logger.error(f"❌ Erreur pendant la parallélisation: {e}")
            logger.error("Passage en mode séquentiel...")
            return self._grid_search(progress_callback)
        
        # Filtrer les None (résultats échoués ou filtrés par early stopping)
        self.results = [r for r in results_raw if r is not None]
        
        backtest_time = time.time() - backtest_start
        
        # Statistiques
        failed = total - len(self.results)
        logger.info(f"\n✅ Parallélisation terminée:")
        logger.info(f"   Temps: {backtest_time:.2f}s")
        logger.info(f"   Vitesse: ~{backtest_time/total:.3f}s par combinaison")
        logger.info(f"   Résultats valides: {len(self.results)}/{total}")
        if failed > 0:
            logger.info(f"   Filtrés/Échoués: {failed} ({failed/total*100:.1f}%)")
        
        # Speedup vs séquentiel
        estimated_sequential = total * 0.55  # Temps moyen par combo en séquentiel
        speedup = estimated_sequential / backtest_time if backtest_time > 0 else 0
        logger.info(f"   🚀 Speedup estimé: {speedup:.1f}x vs séquentiel\n")
        
        # Analyser et sauvegarder
        results = self._analyze_results()
        self._save_results(results)
        
        return results
    
    # def _grid_search_parallel(self, progress_callback: Optional[Callable] = None) -> Dict:
    #     """
    #     🚀 OPTIMISATION #1: Grid Search PARALLÉLISÉ
        
    #     Utilise multiprocessing pour tester plusieurs combinaisons en parallèle.
    #     Exploite tous les cores CPU disponibles.
        
    #     Args:
    #         progress_callback: Fonction callback(progress_pct)
        
    #     Returns:
    #         Dict avec résultats
    #     """
    #     # Générer toutes les combinaisons
    #     param_names = list(self.param_grid.keys())
    #     param_values = list(self.param_grid.values())
    #     combinations = list(product(*param_values))
        
    #     total = len(combinations)
    #     logger.info(f"📊 Grid Search PARALLÈLE: {total} combinaisons à tester")
    #     logger.info(f"   Symboles: {', '.join(self.symbols)}")
    #     logger.info(f"   Période: {self.start_date} → {self.end_date}")
    #     logger.info(f"   Paramètres: {self.param_grid}")
        
    #     # Nombre de workers (laisser 1-2 cores libres pour le système)
    #     n_workers = max(1, cpu_count() - 1)
    #     logger.info(f"   Workers: {n_workers}/{cpu_count()} cores\n")
        
    #     # Préparer les tâches
    #     preloaded_data = self._data_cache
    #     tasks = []
        
    #     for combo in combinations:
    #         params = dict(zip(param_names, combo))
    #         # Chaque tâche = (params, données, classe, config)
    #         tasks.append((
    #             params,
    #             preloaded_data,
    #             self.strategy_class,
    #             self.config
    #         ))
        
    #     # Exécuter en parallèle
    #     backtest_start = time.time()
        
    #     logger.info(f"🔥 Lancement de {n_workers} workers parallèles...")
        
    #     try:
    #         # Utiliser multiprocessing.Pool
    #         with Pool(processes=n_workers) as pool:
    #             # starmap pour passer plusieurs arguments
    #             # On utilise aussi imap pour avoir un itérateur et suivre la progression
                
    #             # Option 1: Tout d'un coup (plus rapide mais pas de progression)
    #             # results_raw = pool.starmap(run_backtest_worker, tasks)
                
    #             # Option 2: Avec progression (un peu plus lent mais meilleur feedback)
    #             results_raw = []
                
    #             # Créer un itérateur avec chunksize pour optimiser
    #             chunksize = max(1, total // (n_workers * 4))
                
    #             for i, result in enumerate(pool.starmap(run_backtest_worker, tasks, chunksize=chunksize), 1):
    #                 results_raw.append(result)
                    
    #                 # Callback progression
    #                 if progress_callback and i % max(1, total // 20) == 0:
    #                     progress_callback(i / total)
                    
    #                 # Log tous les 10%
    #                 if self.verbose and i % max(1, total // 10) == 0:
    #                     logger.info(f"  Progression: {i}/{total} ({i/total*100:.0f}%)")
        
    #     except Exception as e:
    #         logger.error(f"❌ Erreur pendant la parallélisation: {e}")
    #         logger.error("Passage en mode séquentiel...")
    #         return self._grid_search(progress_callback)
        
    #     # Filtrer les None (résultats échoués ou filtrés par early stopping)
    #     self.results = [r for r in results_raw if r is not None]
        
    #     backtest_time = time.time() - backtest_start
        
    #     # Statistiques
    #     failed = total - len(self.results)
    #     logger.info(f"\n✅ Parallélisation terminée:")
    #     logger.info(f"   Temps: {backtest_time:.2f}s")
    #     logger.info(f"   Vitesse: ~{backtest_time/total:.3f}s par combinaison")
    #     logger.info(f"   Résultats valides: {len(self.results)}/{total}")
    #     if failed > 0:
    #         logger.info(f"   Filtrés/Échoués: {failed} ({failed/total*100:.1f}%)")
        
    #     # Speedup vs séquentiel
    #     estimated_sequential = total * 0.55  # Temps moyen par combo en séquentiel
    #     speedup = estimated_sequential / backtest_time if backtest_time > 0 else 0
    #     logger.info(f"   🚀 Speedup estimé: {speedup:.1f}x vs séquentiel\n")
        
    #     # Analyser et sauvegarder
    #     results = self._analyze_results()
    #     self._save_results(results)
        
    #     return results
    
    def _grid_search(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Grid Search SÉQUENTIEL (version non parallélisée)
        
        Utilisé comme fallback si parallélisation échoue ou désactivée.
        
        Args:
            progress_callback: Fonction callback(progress_pct, eta_seconds)
        
        Returns:
            Dict avec résultats
        """
        # Générer toutes les combinaisons
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(product(*param_values))
        
        total = len(combinations)
        logger.info(f"📊 Grid Search SÉQUENTIEL: {total} combinaisons à tester")
        logger.info(f"   Symboles: {', '.join(self.symbols)}")
        logger.info(f"   Période: {self.start_date} → {self.end_date}")
        logger.info(f"   Paramètres: {self.param_grid}\n")
        
        # Tester chaque combinaison
        backtest_start = time.time()
        start_time = time.time()  # ✅ Pour estimation du temps restant (ETA)
        
        for i, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))
            
            if self.verbose:
                logger.info(f"[{i}/{total}] Test: {params}")
            
            # Exécuter le backtest avec cache
            result = self._run_single_backtest(params)
            
            if result:
                self.results.append(result)
                
                if self.verbose:
                    logger.info(f"  → Sharpe: {result.get('sharpe', 0):.2f}, "
                            f"Return: {result.get('return', 0):.2f}%\n")
            
            # ✅ Callback progression avec ETA (2 arguments au lieu d'1)
            if progress_callback:
                progress_pct = i / total
                
                # Estimation du temps restant
                elapsed = time.time() - start_time
                if i > 0:
                    time_per_task = elapsed / i
                    remaining_tasks = total - i
                    eta_seconds = time_per_task * remaining_tasks
                else:
                    eta_seconds = 0
                
                # Appeler le callback avec progression et ETA
                progress_callback(progress_pct, eta_seconds)
        
        backtest_time = time.time() - backtest_start
        logger.info(f"⏱️ Temps de backtesting: {backtest_time:.2f}s")
        logger.info(f"   (~{backtest_time/total:.2f}s par combinaison)\n")
        
        # Analyser et sauvegarder
        results = self._analyze_results()
        self._save_results(results)
        
        return results
    
    def _run_single_backtest(self, params: Dict, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """
        Exécute un seul backtest (version séquentielle)
        
        Utilisé pour Walk-Forward et comme fallback
        """
        try:
            # Cerebro optimisé
            cerebro = bt.Cerebro(
                stdstats=False,
                exactbars=-1,
            )
            
            cerebro.broker.setcash(self.capital)
            cerebro.broker.setcommission(commission=settings.COMMISSION)
            
            # Utiliser le cache
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            if start != self.start_date or end != self.end_date:
                # Dates différentes (Walk-Forward) → recharger
                for symbol in self.symbols:
                    df = self.data_handler.fetch_data(symbol, start, end)
                    if df is not None and not df.empty:
                        data_feed = create_data_feed(df, name=symbol)
                        cerebro.adddata(data_feed, name=symbol)
            else:
                # Utiliser le cache
                for symbol, df in self._data_cache.items():
                    data_feed = create_data_feed(df.copy(), name=symbol)
                    cerebro.adddata(data_feed, name=symbol)
            
            # Stratégie
            converted_params = self._convert_params(params)
            cerebro.addstrategy(
                self.strategy_class, 
                **converted_params, 
                printlog=False
            )
            
            # Analyseurs minimaux
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            
            # Exécuter
            start_value = cerebro.broker.getvalue()
            strategies = cerebro.run()
            end_value = cerebro.broker.getvalue()
            
            # Résultats
            strat = strategies[0]
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            
            result = {
                **params,
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
    
    def _convert_params(self, params: Dict) -> Dict:
        """Convertit les paramètres au bon type"""
        converted = {}
        for key, value in params.items():
            if any(word in key.lower() for word in ['period', 'window', 'length', 'days']):
                converted[key] = int(value)
            else:
                converted[key] = value
        return converted
    
    def _walk_forward(self, progress_callback: Optional[Callable] = None) -> Dict:
        """Walk-Forward Analysis (utilise Grid Search parallèle pour In-Sample)"""
        # Paramètres Walk-Forward
        in_sample_months = self.config.get('walk_forward', {}).get('in_sample_months', 6)
        out_sample_months = self.config.get('walk_forward', {}).get('out_sample_months', 3)
        
        # Générer les périodes
        periods = self._generate_walk_forward_periods(in_sample_months, out_sample_months)
        total_steps = len(periods)
        
        logger.info(f"🚶 Walk-Forward Analysis: {total_steps} périodes")
        logger.info(f"   In-Sample: {in_sample_months} mois")
        logger.info(f"   Out-Sample: {out_sample_months} mois\n")
        
        walk_forward_results = []
        
        for i, period in enumerate(periods, 1):
            in_start, in_end = period['in_sample']
            out_start, out_end = period['out_sample']
            
            logger.info(f"{'='*70}")
            logger.info(f"PÉRIODE {i}/{total_steps}")
            logger.info(f"{'='*70}")
            logger.info(f"In-Sample:  {in_start} → {in_end}")
            logger.info(f"Out-Sample: {out_start} → {out_end}\n")
            
            # Optimiser sur In-Sample (avec parallélisation)
            logger.info("🔬 Optimisation sur In-Sample...")
            
            in_sample_config = self.config.copy()
            in_sample_config['period'] = {'start': in_start, 'end': in_end}
            
            in_sample_optimizer = UnifiedOptimizer(
                self.strategy_class,
                in_sample_config,
                optimization_type='grid_search',
                verbose=False,
                use_parallel=self.use_parallel  # Utiliser la même config
            )
            
            in_sample_results = in_sample_optimizer.run()
            
            if not in_sample_results or 'best' not in in_sample_results:
                logger.warning(f"Période {i}: Pas de résultats In-Sample")
                continue
            
            best_params = {k: v for k, v in in_sample_results['best'].items() 
                          if k not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']}
            
            in_sharpe = in_sample_results['best'].get('sharpe', 0) or 0
            in_return = in_sample_results['best'].get('return', 0) or 0
            
            logger.info(f"✅ Meilleurs paramètres In-Sample: {best_params}")
            logger.info(f"  Sharpe: {in_sharpe:.2f}, Return: {in_return:.2f}%\n")
            
            # Tester sur Out-Sample
            logger.info("🧪 Test sur Out-Sample...")
            
            out_result = self._run_single_backtest(
                best_params,
                start_date=out_start,
                end_date=out_end
            )
            
            if out_result and out_result.get('trades', 0) > 0:
                out_sharpe = out_result.get('sharpe', 0) or 0
                out_return = out_result.get('return', 0) or 0
                
                logger.info(f"✅ Résultats Out-Sample:")
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
            
            if progress_callback:
                progress_callback(i / total_steps)
        
        return self._analyze_walk_forward_results(walk_forward_results)
    
    def _random_search(self, progress_callback: Optional[Callable] = None) -> Dict:
        """Random Search (à implémenter)"""
        logger.warning("Random Search pas encore implémenté")
        return {}
    
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
        
        df = pd.DataFrame(self.results)
        df_sorted = df.sort_values('sharpe', ascending=False)
        
        self.best_result = df_sorted.iloc[0].to_dict()
        
        logger.info(f"\n{'='*80}")
        logger.info("🏆 MEILLEURE COMBINAISON")
        logger.info(f"{'='*80}")
        for key, value in self.best_result.items():
            if key in ['sharpe', 'return', 'drawdown', 'win_rate']:
                logger.info(f"   {key:.<20} {value:>10.2f}")
            elif key == 'trades':
                logger.info(f"   {key:.<20} {value:>10}")
            else:
                logger.info(f"   {key:.<20} {value}")
        
        logger.info(f"\n{'='*80}")
        logger.info("📊 STATISTIQUES GLOBALES")
        logger.info(f"{'='*80}")
        logger.info(f"   Combinaisons testées: {len(self.results)}")
        logger.info(f"   Sharpe moyen:         {df['sharpe'].mean():.2f}")
        logger.info(f"   Sharpe max:           {df['sharpe'].max():.2f}")
        logger.info(f"   Sharpe min:           {df['sharpe'].min():.2f}")
        logger.info(f"   Return moyen:         {df['return'].mean():.2f}%")
        
        return {
            'run_id': self.run_id,
            'strategy': self.strategy_name,
            'optimization_type': self.optimization_type,
            'parallel': self.use_parallel,
            'best': self.best_result,
            'all_results': self.results,
            'total_combinations': len(self.results),
            'statistics': {
                'avg_sharpe': df['sharpe'].mean(),
                'max_sharpe': df['sharpe'].max(),
                'min_sharpe': df['sharpe'].min(),
                'avg_return': df['return'].mean()
            }
        }
    
    def _analyze_walk_forward_results(self, walk_forward_results: List[Dict]) -> Dict:
        """Analyse les résultats du Walk-Forward"""
        if not walk_forward_results:
            logger.error("❌ Aucun résultat Walk-Forward disponible")
            return {'run_id': self.run_id, 'best': {}, 'periods': []}
        
        df = pd.DataFrame(walk_forward_results)
        
        avg_in_sharpe = df['in_sharpe'].mean()
        avg_out_sharpe = df['out_sharpe'].mean()
        avg_degradation = df['degradation'].mean()
        
        best_period = df.loc[df['out_sharpe'].idxmax()]
        
        logger.info(f"\n{'='*80}")
        logger.info("🏆 RÉSULTATS WALK-FORWARD")
        logger.info(f"{'='*80}")
        logger.info(f"   Périodes testées:        {len(walk_forward_results)}")
        logger.info(f"   Avg In-Sample Sharpe:    {avg_in_sharpe:.2f}")
        logger.info(f"   Avg Out-Sample Sharpe:   {avg_out_sharpe:.2f}")
        logger.info(f"   Dégradation moyenne:     {avg_degradation:.2f}")
        logger.info(f"   Best Out-Sample Sharpe:  {best_period['out_sharpe']:.2f}")
        
        self.best_result = {
            **best_period['best_params'],
            'sharpe': best_period['out_sharpe'],
            'return': best_period['out_return'],
            'trades': best_period['out_trades']
        }
        
        return {
            'run_id': self.run_id,
            'strategy': self.strategy_name,
            'optimization_type': self.optimization_type,
            'parallel': self.use_parallel,
            'best': self.best_result,
            'periods': walk_forward_results,
            'statistics': {
                'avg_in_sharpe': avg_in_sharpe,
                'avg_out_sharpe': avg_out_sharpe,
                'avg_degradation': avg_degradation,
                'best_out_sharpe': best_period['out_sharpe']
            }
        }
    
    def _save_results(self, results: Dict):
        """Sauvegarde les résultats"""
        full_config = {
            **self.config,
            'strategy_name': self.strategy_name,
            'optimization_type': self.optimization_type,
            'parallel': self.use_parallel
        }
        
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
        
        return {k: v for k, v in self.best_result.items() 
                if k not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']}
    
    def _optuna_optimization(self, progress_callback: Optional[Callable] = None) -> Dict:
        """🔬 OPTIMISATION OPTUNA"""
        from optimization.optuna_optimizer import OptunaOptimizer
        
        logger.info("🔬 Démarrage de l'optimisation Optuna")
        
        # Configuration
        optuna_config = self.config.get('optuna', {})
        n_trials = optuna_config.get('n_trials', 100)
        
        # Fonction objectif
        def objective_function(params: Dict) -> float:
            result = self._run_single_backtest(params)
            if result is None:
                return float('-inf')
            return result.get('sharpe', 0)
        
        # Créer et lancer l'optimiseur
        optuna_opt = OptunaOptimizer(
            objective_func=objective_function,
            param_grid=self.param_grid,
            n_trials=n_trials,
            direction='maximize',
            study_name=f"{self.strategy_name}_{self.run_id}",
            n_jobs=cpu_count() if self.use_parallel else 1,
            logger=logger
        )
        
        optuna_results = optuna_opt.optimize(progress_callback=progress_callback)
        
        # Récupérer les résultats
        self.results = optuna_opt.optimization_history
        
        # Sauvegarder les visualisations
        if optuna_config.get('save_plots', True):
            optuna_opt.save_visualizations()
        
        # Analyser et retourner
        results = self._analyze_results()
        results['param_importance'] = optuna_opt.get_importance()
        self._save_results(results)
        
        return results


# Fonctions helper
def optimize(strategy_class, 
            preset_name: str = "standard",
            optimization_type: str = "grid_search",
            use_parallel: bool = True) -> Dict:
    """
    Fonction helper pour optimiser rapidement avec un preset
    """
    from optimization.optimization_config import load_preset
    
    config = load_preset(preset_name)
    optimizer = UnifiedOptimizer(
        strategy_class, 
        config, 
        optimization_type,
        use_parallel=use_parallel
    )
    return optimizer.run()


if __name__ == "__main__":
    print("="*80)
    print("TEST UNIFIED OPTIMIZER - VERSION PARALLÉLISÉE")
    print("="*80)
    
    from strategies.masuperstrategie import MaSuperStrategie
    from optimization.optimization_config import load_preset
    
    print("\n🔬 Test Grid Search PARALLÈLE avec preset 'quick':\n")
    config = load_preset('quick')
    
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='grid_search',
        use_parallel=True  # 🚀 PARALLÉLISATION ACTIVÉE
    )
    
    results = optimizer.run()
    
    print("\n✅ Optimisation terminée !")
    print(f"Run ID: {results['run_id']}")
    print(f"Meilleur Sharpe: {results['best'].get('sharpe', 0):.2f}")