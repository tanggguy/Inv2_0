#!/usr/bin/env python3
"""
Fonctions Worker pour Multiprocessing

Ces fonctions doivent être au niveau module (pas dans une classe)
pour être sérialisables par multiprocessing (pickle).
"""

import backtrader as bt
import pandas as pd
from typing import Dict, Optional

from config import settings
from data.data_fetcher import create_data_feed
from utils.metrics_validator import safe_calculate_return , MetricsValidator

def run_backtest_worker(params: Dict,
                       preloaded_data: Dict[str, pd.DataFrame],
                       strategy_class,
                       config: Dict) -> Optional[Dict]:
    """
    Worker fonction pour exécuter un backtest en parallèle
    
    🎯 IMPORTANT: Cette fonction doit être au niveau module pour pickling
    
    Args:
        params: Paramètres de la stratégie à tester
        preloaded_data: Dict {symbol: DataFrame} avec données pré-chargées
        strategy_class: Classe de la stratégie
        config: Configuration globale
    
    Returns:
        Dict avec résultats ou None si échec
    """
    try:
        # Extraire la config
        capital = config.get('capital', 100000)
        
        # Créer Cerebro optimisé
        cerebro = bt.Cerebro(
            stdstats=False,  # Pas d'observers
            exactbars=-1,    # Mode mémoire optimisé
        )
        
        cerebro.broker.setcash(capital)
        cerebro.broker.setcommission(commission=settings.COMMISSION)
        
        # Charger les données depuis le cache
        for symbol, df in preloaded_data.items():
            # IMPORTANT: .copy() pour éviter modification du cache
            data_feed = create_data_feed(df.copy(), name=symbol)
            cerebro.adddata(data_feed, name=symbol)
        
        # Convertir les paramètres au bon type
        converted_params = _convert_params(params)
        
        # Ajouter la stratégie
        cerebro.addstrategy(
            strategy_class,
            **converted_params,
            printlog=False  # Pas de logs
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
        
        # Récupérer les résultats
        strat = strategies[0]
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        
        total_trades = trades.get('total', {}).get('total', 0)
        won_trades = trades.get('won', {}).get('total', 0)
        
        # 🚀 EARLY STOPPING OPTIONNEL
        # Filtrer les résultats catastrophiques rapidement
        

        total_return = safe_calculate_return(start_value, end_value)

        
        if total_return < -50:  # Perte > 50%
            return None
        
        if total_trades < 3:  # Pas assez de trades
            return None
        
        # Construire le résultat
        result = {
            **params,  # Inclure les paramètres
            'sharpe': sharpe.get('sharperatio', 0) or 0,
            'return': total_return,
            'drawdown': drawdown.get('max', {}).get('drawdown', 0),
            'trades': total_trades,
            'win_rate': (won_trades / total_trades * 100) if total_trades > 0 else 0
        }
        validator = MetricsValidator()
        result = validator.validate_and_clean(result)
        return result
        
    except Exception as e:
        # En cas d'erreur, retourner None
        # Les erreurs seront loggées dans le processus principal
        return None


def _convert_params(params: Dict) -> Dict:
    """
    Convertit les paramètres au bon type
    (certains paramètres doivent être int au lieu de float)
    
    Args:
        params: Paramètres bruts
    
    Returns:
        Paramètres convertis
    """
    converted = {}
    for key, value in params.items():
        # Si le paramètre contient 'period', 'window', 'length' → convertir en int
        if any(word in key.lower() for word in ['period', 'window', 'length', 'days']):
            converted[key] = int(value)
        else:
            converted[key] = value
    return converted


def run_backtest_worker_with_dates(params: Dict,
                                   preloaded_data: Dict[str, pd.DataFrame],
                                   strategy_class,
                                   config: Dict,
                                   start_date: str,
                                   end_date: str) -> Optional[Dict]:
    """
    Worker pour Walk-Forward avec dates spécifiques
    
    Args:
        params: Paramètres de la stratégie
        preloaded_data: Données pré-chargées (ignorées si dates différentes)
        strategy_class: Classe de la stratégie
        config: Configuration
        start_date: Date de début
        end_date: Date de fin
    
    Returns:
        Dict avec résultats ou None
    """
    try:
        # Pour Walk-Forward, il faut recharger les données avec les bonnes dates
        # Car chaque période a des dates différentes
        
        from data.data_handler import DataHandler
        
        capital = config.get('capital', 100000)
        symbols = config.get('symbols', ['AAPL'])
        
        # Créer Cerebro optimisé
        cerebro = bt.Cerebro(
            stdstats=False,
            exactbars=-1,
        )
        
        cerebro.broker.setcash(capital)
        cerebro.broker.setcommission(commission=settings.COMMISSION)
        
        # Charger les données pour cette période spécifique
        data_handler = DataHandler()
        
        for symbol in symbols:
            df = data_handler.fetch_data(symbol, start_date, end_date)
            if df is not None and not df.empty:
                data_feed = create_data_feed(df, name=symbol)
                cerebro.adddata(data_feed, name=symbol)
        
        # Convertir paramètres
        converted_params = _convert_params(params)
        
        # Ajouter stratégie
        cerebro.addstrategy(
            strategy_class,
            **converted_params,
            printlog=False
        )
        
        # Analyseurs
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
            'return': ((end_value - start_value) / start_value) * 100 if start_value > 0 else 0,
            'drawdown': drawdown.get('max', {}).get('drawdown', 0),
            'trades': total_trades,
            'win_rate': (won_trades / total_trades * 100) if total_trades > 0 else 0
        }
        
        return result
        
    except Exception as e:
        return None