#!/usr/bin/env python3
"""
Gestion du stockage et de l'historique des résultats d'optimisation
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from monitoring.logger import setup_logger

logger = setup_logger("results_storage")


class ResultsStorage:
    """Gère le stockage et l'historique des résultats d'optimisation"""
    
    def __init__(self, base_dir: str = "results"):
        self.base_dir = Path(base_dir)
        self.history_dir = self.base_dir / "history"
        self.details_dir = self.base_dir / "details"
        self.cache_dir = self.base_dir / "cache"
        
        # Créer les dossiers
        for directory in [self.history_dir, self.details_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "optimization_runs.json"
        
        # Initialiser le fichier d'historique si nécessaire
        if not self.history_file.exists():
            self._init_history_file()
        
        logger.info(f"ResultsStorage initialisé: {self.base_dir}")
    
    def _init_history_file(self):
        """Initialise le fichier d'historique"""
        initial_data = {
            "runs": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_runs": 0
            }
        }
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        logger.info("✓ Fichier d'historique initialisé")
    
    def generate_run_id(self, strategy_name: str, optimization_type: str) -> str:
        """
        Génère un ID unique pour un run
        
        Args:
            strategy_name: Nom de la stratégie
            optimization_type: Type d'optimisation
        
        Returns:
            ID unique (ex: opt_MaSuperStrategie_grid_20250104_143022)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"opt_{strategy_name}_{optimization_type}_{timestamp}"
        return run_id
    
    def save_run(self, 
                 run_id: str,
                 config: Dict,
                 results: Dict,
                 optimization_type: str = "grid_search") -> bool:
        """
        Sauvegarde un run d'optimisation complet
        
        Args:
            run_id: ID unique du run
            config: Configuration utilisée
            results: Résultats de l'optimisation
            optimization_type: Type d'optimisation
        
        Returns:
            True si sauvegarde réussie
        """
        try:
            # Créer le dossier pour ce run
            run_dir = self.details_dir / run_id
            run_dir.mkdir(exist_ok=True)
            
            # Sauvegarder la config
            config_file = run_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder les résultats détaillés en CSV
            if 'all_results' in results and results['all_results']:
                results_df = pd.DataFrame(results['all_results'])
                results_csv = run_dir / "results.csv"
                results_df.to_csv(results_csv, index=False)
                logger.info(f"  ✓ {len(results_df)} résultats sauvegardés en CSV")
            
            # Créer un résumé
            summary = self._create_summary(config, results, optimization_type)
            summary_file = run_dir / "summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Ajouter à l'historique
            self._add_to_history(run_id, summary)
            
            logger.info(f"✓ Run '{run_id}' sauvegardé avec succès dans {run_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du run: {e}")
            return False
    
    def _create_summary(self, config: Dict, results: Dict, optimization_type: str) -> Dict:
        """Crée un résumé du run"""
        
        # Extraire les meilleurs résultats
        best_result = results.get('best', {})
        
        # Calculer des stats sur tous les résultats
        all_results = results.get('all_results', [])
        stats = {}
        
        if all_results:
            df = pd.DataFrame(all_results)
            stats = {
                'mean_sharpe': float(df['sharpe'].mean()) if 'sharpe' in df else 0,
                'std_sharpe': float(df['sharpe'].std()) if 'sharpe' in df else 0,
                'mean_return': float(df['return'].mean()) if 'return' in df else 0,
                'std_return': float(df['return'].std()) if 'return' in df else 0,
                'best_sharpe': float(df['sharpe'].max()) if 'sharpe' in df else 0,
                'worst_sharpe': float(df['sharpe'].min()) if 'sharpe' in df else 0,
            }
        
        summary = {
            'run_id': results.get('run_id', ''),
            'timestamp': datetime.now().isoformat(),
            'strategy': config.get('strategy_name', 'Unknown'),
            'optimization_type': optimization_type,
            'symbols': config.get('symbols', []),
            'period': config.get('period', {}),
            'total_combinations': len(all_results),
            'best_params': best_result,
            'statistics': stats,
            'config_name': config.get('name', 'Custom')
        }
        
        return summary
    
    def _add_to_history(self, run_id: str, summary: Dict):
        """Ajoute un run à l'historique"""
        try:
            # Charger l'historique actuel
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Créer l'entrée d'historique
            entry = {
                'run_id': run_id,
                'timestamp': summary['timestamp'],
                'strategy': summary['strategy'],
                'type': summary['optimization_type'],
                'best_sharpe': summary['best_params'].get('sharpe', 0),
                'best_return': summary['best_params'].get('return', 0),
                'total_combos': summary['total_combinations'],
                'symbols': summary['symbols'],
                'period': summary['period'],
                'path': f"details/{run_id}"
            }
            
            # Ajouter à la liste
            history['runs'].append(entry)
            history['metadata']['total_runs'] = len(history['runs'])
            history['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Sauvegarder
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Ajouté à l'historique: {run_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à l'historique: {e}")
    
    def load_run(self, run_id: str) -> Optional[Dict]:
        """
        Charge les détails d'un run spécifique
        
        Args:
            run_id: ID du run
        
        Returns:
            Dict avec config, results, summary ou None
        """
        run_dir = self.details_dir / run_id
        
        if not run_dir.exists():
            logger.warning(f"Run '{run_id}' introuvable")
            return None
        
        try:
            # Charger config
            with open(run_dir / "config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Charger summary
            with open(run_dir / "summary.json", 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            # Charger results CSV si existe
            results_csv = run_dir / "results.csv"
            results_df = None
            if results_csv.exists():
                results_df = pd.read_csv(results_csv)
            
            data = {
                'run_id': run_id,
                'config': config,
                'summary': summary,
                'results_df': results_df,
                'path': str(run_dir)
            }
            
            logger.info(f"✓ Run '{run_id}' chargé")
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du run: {e}")
            return None
    
    def list_runs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Liste tous les runs avec filtres optionnels
        
        Args:
            filters: Dict avec filtres optionnels
                - strategy: str ou list
                - min_sharpe: float
                - max_sharpe: float
                - symbols: list
                - start_date: str (YYYY-MM-DD)
                - end_date: str (YYYY-MM-DD)
                - type: str (grid_search, walk_forward, etc.)
        
        Returns:
            Liste de runs filtrés
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            runs = history.get('runs', [])
            
            if not filters:
                return runs
            
            # Appliquer les filtres
            filtered = runs
            
            # Filtre par stratégie
            if 'strategy' in filters:
                strategies = filters['strategy'] if isinstance(filters['strategy'], list) else [filters['strategy']]
                filtered = [r for r in filtered if r['strategy'] in strategies]
            
            # Filtre par Sharpe
            if 'min_sharpe' in filters:
                filtered = [r for r in filtered if r.get('best_sharpe', 0) >= filters['min_sharpe']]
            
            if 'max_sharpe' in filters:
                filtered = [r for r in filtered if r.get('best_sharpe', 0) <= filters['max_sharpe']]
            
            # Filtre par type
            if 'type' in filters:
                filtered = [r for r in filtered if r.get('type') == filters['type']]
            
            # Filtre par symboles
            if 'symbols' in filters:
                symbols_filter = set(filters['symbols'])
                filtered = [r for r in filtered if any(s in r.get('symbols', []) for s in symbols_filter)]
            
            # Filtre par date
            if 'start_date' in filters:
                start = datetime.fromisoformat(filters['start_date'])
                filtered = [r for r in filtered if datetime.fromisoformat(r['timestamp']) >= start]
            
            if 'end_date' in filters:
                end = datetime.fromisoformat(filters['end_date'])
                filtered = [r for r in filtered if datetime.fromisoformat(r['timestamp']) <= end]
            
            logger.info(f"Runs listés: {len(filtered)}/{len(runs)} (avec filtres)")
            return filtered
            
        except Exception as e:
            logger.error(f"Erreur lors du listing: {e}")
            return []
    
    def compare_runs(self, run_ids: List[str]) -> Optional[pd.DataFrame]:
        """
        Compare plusieurs runs
        
        Args:
            run_ids: Liste des IDs à comparer
        
        Returns:
            DataFrame comparatif ou None
        """
        if len(run_ids) < 2:
            logger.warning("Au moins 2 runs nécessaires pour comparaison")
            return None
        
        comparison_data = []
        
        for run_id in run_ids:
            run_data = self.load_run(run_id)
            if run_data:
                summary = run_data['summary']
                best = summary.get('best_params', {})
                
                row = {
                    'run_id': run_id,
                    'strategy': summary.get('strategy'),
                    'type': summary.get('optimization_type'),
                    'sharpe': best.get('sharpe', 0),
                    'return': best.get('return', 0),
                    'drawdown': best.get('drawdown', 0),
                    'trades': best.get('trades', 0),
                    'win_rate': best.get('win_rate', 0),
                    'symbols': ', '.join(summary.get('symbols', [])),
                    'timestamp': summary.get('timestamp')
                }
                
                # Ajouter les meilleurs paramètres
                for key, value in best.items():
                    if key not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']:
                        row[f'param_{key}'] = value
                
                comparison_data.append(row)
        
        if not comparison_data:
            logger.warning("Aucune donnée à comparer")
            return None
        
        df = pd.DataFrame(comparison_data)
        logger.info(f"✓ Comparaison de {len(df)} runs")
        return df
    
    def get_best_run(self, strategy: Optional[str] = None, metric: str = 'sharpe') -> Optional[Dict]:
        """
        Récupère le meilleur run selon une métrique
        
        Args:
            strategy: Filtrer par stratégie (optionnel)
            metric: Métrique à utiliser ('sharpe', 'return', etc.)
        
        Returns:
            Meilleur run ou None
        """
        filters = {'strategy': strategy} if strategy else None
        runs = self.list_runs(filters)
        
        if not runs:
            return None
        
        metric_key = f'best_{metric}' if not metric.startswith('best_') else metric
        best = max(runs, key=lambda r: r.get(metric_key, 0))
        
        logger.info(f"Meilleur run: {best['run_id']} ({metric}={best.get(metric_key, 0):.2f})")
        return best
    
    def get_statistics(self) -> Dict:
        """
        Récupère des statistiques globales
        
        Returns:
            Dict avec stats
        """
        runs = self.list_runs()
        
        if not runs:
            return {
                'total_runs': 0,
                'total_strategies': 0,
                'best_sharpe': 0,
                'best_return': 0
            }
        
        df = pd.DataFrame(runs)
        
        stats = {
            'total_runs': len(runs),
            'total_strategies': df['strategy'].nunique() if 'strategy' in df else 0,
            'best_sharpe': float(df['best_sharpe'].max()) if 'best_sharpe' in df else 0,
            'best_return': float(df['best_return'].max()) if 'best_return' in df else 0,
            'avg_sharpe': float(df['best_sharpe'].mean()) if 'best_sharpe' in df else 0,
            'avg_return': float(df['best_return'].mean()) if 'best_return' in df else 0,
            'strategies': list(df['strategy'].unique()) if 'strategy' in df else [],
            'optimization_types': list(df['type'].unique()) if 'type' in df else []
        }
        
        return stats
    
    def delete_run(self, run_id: str) -> bool:
        """
        Supprime un run
        
        Args:
            run_id: ID du run à supprimer
        
        Returns:
            True si suppression réussie
        """
        try:
            # Supprimer le dossier
            run_dir = self.details_dir / run_id
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)
            
            # Retirer de l'historique
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            history['runs'] = [r for r in history['runs'] if r['run_id'] != run_id]
            history['metadata']['total_runs'] = len(history['runs'])
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Run '{run_id}' supprimé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False


# Test du module
if __name__ == "__main__":
    print("="*70)
    print("TEST DU MODULE RESULTS STORAGE")
    print("="*70)
    
    storage = ResultsStorage()
    
    # Test 1: Générer un run_id
    print("\n📝 Génération d'un run ID:")
    run_id = storage.generate_run_id("MaSuperStrategie", "grid_search")
    print(f"  Run ID: {run_id}")
    
    # Test 2: Sauvegarder un run simulé
    print("\n💾 Sauvegarde d'un run de test:")
    test_config = {
        'strategy_name': 'MaSuperStrategie',
        'symbols': ['AAPL', 'MSFT'],
        'period': {'start': '2022-01-01', 'end': '2024-01-01'},
        'name': 'Test Run',
        'param_grid': {'ma_period': [20, 50], 'rsi_period': [14]}
    }
    
    test_results = {
        'run_id': run_id,
        'best': {
            'sharpe': 2.34,
            'return': 45.2,
            'drawdown': -12.5,
            'ma_period': 20,
            'rsi_period': 14
        },
        'all_results': [
            {'sharpe': 2.34, 'return': 45.2, 'ma_period': 20, 'rsi_period': 14},
            {'sharpe': 1.89, 'return': 32.1, 'ma_period': 50, 'rsi_period': 14}
        ]
    }
    
    success = storage.save_run(run_id, test_config, test_results, "grid_search")
    print(f"  Sauvegarde: {'✓' if success else '✗'}")
    
    # Test 3: Lister les runs
    print("\n📋 Liste des runs:")
    runs = storage.list_runs()
    for run in runs:
        print(f"  • {run['run_id']} - {run['strategy']} - Sharpe: {run['best_sharpe']:.2f}")
    
    # Test 4: Charger un run
    print(f"\n📂 Chargement du run '{run_id}':")
    loaded = storage.load_run(run_id)
    if loaded:
        print(f"  ✓ Run chargé:")
        print(f"    Strategy: {loaded['summary']['strategy']}")
        print(f"    Best Sharpe: {loaded['summary']['best_params']['sharpe']:.2f}")
    
    # Test 5: Statistiques
    print("\n📊 Statistiques globales:")
    stats = storage.get_statistics()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print("\n✓ Tests terminés avec succès !")