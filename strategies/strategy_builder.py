"""
═══════════════════════════════════════════════════════════════════════════════
    STRATEGY BUILDER - Créateur de Stratégies Programmatique
═══════════════════════════════════════════════════════════════════════════════

Builder pour créer des stratégies de trading rapidement et facilement

Utilisation:
    from strategies.strategy_builder import StrategyBuilder
    
    strategy = (StrategyBuilder('MaStrategie')
               .add_indicator('SMA', period=20)
               .add_indicator('RSI', period=14)
               .with_stop_loss(0.02)
               .with_trailing_stop(0.03)
               .build())

Sauvegardez dans: strategies/strategy_builder.py
"""

import backtrader as bt
from strategies.advanced_strategies import BaseAdvancedStrategy


class StrategyBuilder:
    """
    Builder pour créer des stratégies rapidement
    
    Exemple:
        strategy = (StrategyBuilder()
                   .add_indicator('SMA', period=20)
                   .add_indicator('RSI', period=14)
                   .with_stop_loss(0.02)
                   .with_trailing_stop(0.03)
                   .build())
    """
    
    def __init__(self, name="CustomStrategy"):
        self.name = name
        self.indicators = []
        self.entry_conditions = []
        self.exit_conditions = []
        self.stop_loss_config = None
        self.take_profit_config = None
        self.trailing_stop_config = None
    
    def add_indicator(self, indicator_type, **params):
        """
        Ajoute un indicateur
        
        Args:
            indicator_type: Type d'indicateur ('SMA', 'EMA', 'RSI', 'MACD', 'Bollinger')
            **params: Paramètres de l'indicateur
        
        Returns:
            self pour chaînage
        """
        self.indicators.append({
            'type': indicator_type,
            'params': params
        })
        return self
    
    def add_entry_condition(self, condition_func):
        """
        Ajoute une condition d'entrée
        
        Args:
            condition_func: Fonction qui retourne True/False
        
        Returns:
            self pour chaînage
        """
        self.entry_conditions.append(condition_func)
        return self
    
    def add_exit_condition(self, condition_func):
        """
        Ajoute une condition de sortie
        
        Args:
            condition_func: Fonction qui retourne True/False
        
        Returns:
            self pour chaînage
        """
        self.exit_conditions.append(condition_func)
        return self
    
    def with_stop_loss(self, percentage=None, atr_mult=None):
        """
        Configure le stop loss
        
        Args:
            percentage: Pourcentage de stop loss (ex: 0.02 pour 2%)
            atr_mult: Multiplicateur ATR (ex: 2.0 pour 2x ATR)
        
        Returns:
            self pour chaînage
        """
        self.stop_loss_config = {
            'enabled': True,
            'percentage': percentage,
            'atr_mult': atr_mult
        }
        return self
    
    def with_take_profit(self, percentage=None, risk_reward=None):
        """
        Configure le take profit
        
        Args:
            percentage: Pourcentage de profit (ex: 0.05 pour 5%)
            risk_reward: Ratio risque/rendement (ex: 2.5 pour 2.5:1)
        
        Returns:
            self pour chaînage
        """
        self.take_profit_config = {
            'enabled': True,
            'percentage': percentage,
            'risk_reward': risk_reward
        }
        return self
    
    def with_trailing_stop(self, percentage, activation=0.02):
        """
        Configure le trailing stop
        
        Args:
            percentage: Pourcentage de trailing (ex: 0.03 pour 3%)
            activation: Gain minimum avant activation (ex: 0.02 pour 2%)
        
        Returns:
            self pour chaînage
        """
        self.trailing_stop_config = {
            'enabled': True,
            'percentage': percentage,
            'activation': activation
        }
        return self
    
    def build(self):
        """
        Génère la classe de stratégie
        
        Returns:
            Classe de stratégie prête à être utilisée
        """
        # Créer les paramètres
        params = []
        
        if self.stop_loss_config:
            params.append(('use_stop_loss', True))
            if self.stop_loss_config.get('percentage'):
                params.append(('stop_loss_pct', self.stop_loss_config['percentage']))
            if self.stop_loss_config.get('atr_mult'):
                params.append(('use_atr_stop', True))
                params.append(('stop_loss_atr_mult', self.stop_loss_config['atr_mult']))
        
        if self.take_profit_config:
            params.append(('use_take_profit', True))
            if self.take_profit_config.get('percentage'):
                params.append(('take_profit_pct', self.take_profit_config['percentage']))
            if self.take_profit_config.get('risk_reward'):
                params.append(('risk_reward_ratio', self.take_profit_config['risk_reward']))
        
        if self.trailing_stop_config:
            params.append(('use_trailing_stop', True))
            params.append(('trailing_stop_pct', self.trailing_stop_config['percentage']))
            params.append(('trailing_activation_pct', self.trailing_stop_config['activation']))
        
        # Créer la classe dynamiquement
        class DynamicStrategy(BaseAdvancedStrategy):
            params = tuple(params) if params else ()
            
            def __init__(self):
                super().__init__()
                # Créer les indicateurs
                self._indicators = {}
                for ind_config in self.indicators:
                    ind_type = ind_config['type']
                    ind_params = ind_config['params']
                    
                    if ind_type == 'SMA':
                        self._indicators['sma'] = bt.indicators.SMA(
                            self.datas[0].close,
                            period=ind_params.get('period', 20)
                        )
                    elif ind_type == 'EMA':
                        self._indicators['ema'] = bt.indicators.EMA(
                            self.datas[0].close,
                            period=ind_params.get('period', 20)
                        )
                    elif ind_type == 'RSI':
                        self._indicators['rsi'] = bt.indicators.RSI(
                            self.datas[0].close,
                            period=ind_params.get('period', 14)
                        )
                    elif ind_type == 'MACD':
                        self._indicators['macd'] = bt.indicators.MACD(
                            self.datas[0].close
                        )
                    elif ind_type == 'Bollinger':
                        self._indicators['bollinger'] = bt.indicators.BollingerBands(
                            self.datas[0].close,
                            period=ind_params.get('period', 20),
                            devfactor=ind_params.get('devfactor', 2.0)
                        )
                    elif ind_type == 'ATR':
                        self._indicators['atr'] = bt.indicators.ATR(
                            self.datas[0],
                            period=ind_params.get('period', 14)
                        )
                    elif ind_type == 'Stochastic':
                        self._indicators['stochastic'] = bt.indicators.Stochastic(
                            self.datas[0],
                            period=ind_params.get('period', 14)
                        )
            
            def next(self):
                # Vérifier les stops
                if self._check_stops():
                    return
                
                if self.order:
                    return
                
                # Logique d'entrée
                if not self.position:
                    # Vérifier toutes les conditions d'entrée
                    if all(cond(self) for cond in self.entry_conditions):
                        size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                        self.order = self.buy(size=size)
                else:
                    # Vérifier les conditions de sortie
                    if any(cond(self) for cond in self.exit_conditions):
                        self.order = self.sell(size=self.position.size)
        
        # Copier les données du builder
        DynamicStrategy.indicators = self.indicators
        DynamicStrategy.entry_conditions = self.entry_conditions
        DynamicStrategy.exit_conditions = self.exit_conditions
        DynamicStrategy.__name__ = self.name
        
        return DynamicStrategy


# ═══════════════════════════════════════════════════════════════════════════
# FONCTIONS HELPER POUR LES CONDITIONS
# ═══════════════════════════════════════════════════════════════════════════

def crossover_above(ind1_name, ind2_name):
    """
    Condition: ind1 croise au-dessus de ind2
    
    Args:
        ind1_name: Nom du premier indicateur
        ind2_name: Nom du second indicateur
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind1 = strategy._indicators.get(ind1_name)
        ind2 = strategy._indicators.get(ind2_name)
        if ind1 is None or ind2 is None:
            return False
        return ind1[0] > ind2[0] and ind1[-1] <= ind2[-1]
    return condition


def crossover_below(ind1_name, ind2_name):
    """
    Condition: ind1 croise en-dessous de ind2
    
    Args:
        ind1_name: Nom du premier indicateur
        ind2_name: Nom du second indicateur
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind1 = strategy._indicators.get(ind1_name)
        ind2 = strategy._indicators.get(ind2_name)
        if ind1 is None or ind2 is None:
            return False
        return ind1[0] < ind2[0] and ind1[-1] >= ind2[-1]
    return condition


def above_threshold(ind_name, value):
    """
    Condition: indicateur au-dessus d'un seuil
    
    Args:
        ind_name: Nom de l'indicateur
        value: Seuil
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind = strategy._indicators.get(ind_name)
        if ind is None:
            return False
        return ind[0] > value
    return condition


def below_threshold(ind_name, value):
    """
    Condition: indicateur en-dessous d'un seuil
    
    Args:
        ind_name: Nom de l'indicateur
        value: Seuil
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind = strategy._indicators.get(ind_name)
        if ind is None:
            return False
        return ind[0] < value
    return condition


def price_above_indicator(ind_name):
    """
    Condition: prix au-dessus d'un indicateur
    
    Args:
        ind_name: Nom de l'indicateur
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind = strategy._indicators.get(ind_name)
        if ind is None:
            return False
        return strategy.datas[0].close[0] > ind[0]
    return condition


def price_below_indicator(ind_name):
    """
    Condition: prix en-dessous d'un indicateur
    
    Args:
        ind_name: Nom de l'indicateur
    
    Returns:
        Fonction de condition
    """
    def condition(strategy):
        ind = strategy._indicators.get(ind_name)
        if ind is None:
            return False
        return strategy.datas[0].close[0] < ind[0]
    return condition


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Exemple d'utilisation du StrategyBuilder
    """
    
    # Créer une stratégie simple
    strategy_class = (
        StrategyBuilder('MaSimpleStrategy')
        .add_indicator('SMA', period=20, name='sma_fast')
        .add_indicator('SMA', period=50, name='sma_slow')
        .add_indicator('RSI', period=14, name='rsi')
        .add_entry_condition(crossover_above('sma_fast', 'sma_slow'))
        .add_entry_condition(below_threshold('rsi', 70))
        .add_exit_condition(crossover_below('sma_fast', 'sma_slow'))
        .with_stop_loss(percentage=0.02)
        .with_take_profit(risk_reward=2.5)
        .with_trailing_stop(percentage=0.03, activation=0.02)
        .build()
    )
    
    print(f"Stratégie '{strategy_class.__name__}' créée avec succès!")
    print(f"Paramètres: {strategy_class.params}")