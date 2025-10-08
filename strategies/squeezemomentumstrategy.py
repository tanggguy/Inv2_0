"""
Squeeze Momentum Strategy V2 - VERSION CORRIGÉE ET AMÉLIORÉE
==============================================================

Stratégie basée sur la détection de périodes de consolidation (squeeze) 
suivies de breakouts explosifs avec confirmation de tendance.

CORRECTIONS MAJEURES:
- ✅ Bug logique conditions d'entrée corrigé
- ✅ Paramètres ADX optimisés
- ✅ Logique ATR améliorée
- ✅ Double vérification prix supprimée
- ✅ Filtres de contexte marché ajoutés

NOUVELLES FONCTIONNALITÉS:
- 📊 Filtres tendance long terme (SMA 200)
- 📈 Filtre RSI pour éviter surachat
- 📉 Validation momentum ADX croissant
- 🎯 Meilleure traçabilité du squeeze
- 📊 Stats détaillées des trades

Indicateurs:
- Bollinger Bands (20, 2)
- Keltner Channels (20, 2)
- ATR (14)
- Volume SMA (20)
- ADX (14)
- SMA 200 (tendance long terme)
- RSI (14)

Logique Améliorée:
1. Squeeze: Bollinger dans Keltner (5+ jours consécutifs)
2. Durant squeeze: ADX < 25, volume faible, ATR contracté
3. Breakout: Prix > BB Upper, bougie haussière
4. Confirmation: Volume >2× moyenne, ADX >20 ET croissant
5. Filtres: Prix > SMA 200, RSI < 75
6. Sorties: Stop Loss (BB Mid), Target (2× squeeze height), Trailing (BB Lower)
"""

import backtrader as bt
from strategies.base_strategy import BaseStrategy
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# INDICATEUR PERSONNALISÉ: KELTNER CHANNELS
# ═══════════════════════════════════════════════════════════════════════════

class KeltnerChannels(bt.Indicator):
    """
    Keltner Channels
    
    Middle Line = EMA(period)
    Upper Band = EMA + (multiplier × ATR)
    Lower Band = EMA - (multiplier × ATR)
    """
    lines = ('mid', 'top', 'bot')
    params = (
        ('period', 20),
        ('atr_period', 20),
        ('multiplier', 2.0),
    )
    
    def __init__(self):
        self.lines.mid = bt.indicators.EMA(
            self.data.close, 
            period=self.params.period
        )
        atr = bt.indicators.ATR(
            self.data, 
            period=self.params.atr_period
        )
        self.lines.top = self.lines.mid + (atr * self.params.multiplier)
        self.lines.bot = self.lines.mid - (atr * self.params.multiplier)


# ═══════════════════════════════════════════════════════════════════════════
# STRATÉGIE SQUEEZE MOMENTUM V2 - CORRIGÉE ET AMÉLIORÉE
# ═══════════════════════════════════════════════════════════════════════════

class SqueezeMomentumStrategy(BaseStrategy):
    """
    Stratégie Squeeze Momentum V2 - Version Corrigée
    
    Trade les breakouts après consolidation avec filtres de contexte marché
    Long uniquement avec gestion avancée des stops
    """
    
    params = (
        # ═══════════════════════════════════════════════════════════════
        # FILTRES PRÉALABLES
        # ═══════════════════════════════════════════════════════════════
        ('use_min_volume_ratio', False),
        ('min_volume_ratio', 0.9),      # Volume moyen minimum (liquidité)
        # ('min_price', 5.0),               # Prix minimum (éviter penny stocks)
        
        # ═══════════════════════════════════════════════════════════════
        # PÉRIODES DES INDICATEURS
        # ═══════════════════════════════════════════════════════════════
        ('bb_period', 20),
        ('bb_std', 2.0),
        ('keltner_period', 20),
        ('keltner_mult', 2.0),
        ('atr_period', 14),
        ('volume_period', 20),
        ('adx_period', 14),
        ('sma_long_period', 200),         # Tendance long terme
        ('rsi_period', 14),
        
        # ═══════════════════════════════════════════════════════════════
        # CONDITIONS SQUEEZE (CORRIGÉES)
        # ═══════════════════════════════════════════════════════════════
        ('min_squeeze_days', 3),          # Minimum 5 jours de squeeze consécutifs
        ('squeeze_adx_max', 35),          # ✅ ADX < 25 durant squeeze (moins restrictif)
        ('squeeze_volume_factor', 1.2),   # Volume moyen < 90% de la SMA
        ('squeeze_atr_factor', 1.3),      # ATR moyen < 110% de la SMA ATR
        
        # ═══════════════════════════════════════════════════════════════
        # CONDITIONS BREAKOUT (OPTIMISÉES)
        # ═══════════════════════════════════════════════════════════════
        ('breakout_volume_mult', 1.0),    # ✅ Volume >2× moyenne (plus sélectif)
        ('breakout_adx_min', 12),         # ✅ ADX >20 au breakout (vraie tendance)
        ('require_adx_rising', False),     # ✅ ADX doit être croissant
        ('min_candle_body_pct', 0.2),     # Bougie doit avoir 30% de corps minimum
        
        # ═══════════════════════════════════════════════════════════════
        # FILTRES CONTEXTE MARCHÉ (NOUVEAUX)
        # ═══════════════════════════════════════════════════════════════
        ('use_trend_filter', False),       # Filtrer par SMA 200
        ('use_rsi_filter', False),         # Éviter surachat extrême
        ('rsi_max', 80),                  # RSI max pour entrer
        
        # ═══════════════════════════════════════════════════════════════
        # GESTION DES SORTIES
        # ═══════════════════════════════════════════════════════════════
        ('target_multiplier', 2.0),       # Target = squeeze height × 2
        ('use_trailing_stop', True),      # Activer trailing stop
        ('trailing_stop_activation', 1.5), # Activer trailing après 1.5× squeeze height
        
        # ═══════════════════════════════════════════════════════════════
        # POSITION SIZING
        # ═══════════════════════════════════════════════════════════════
        ('risk_per_trade', 0.02),         # 2% de risque par trade
        ('max_position_pct', 0.2),        # Max 20% du capital par position
        
        # ═══════════════════════════════════════════════════════════════
        # LOGGING
        # ═══════════════════════════════════════════════════════════════
        ('printlog', True),
        ('debug_mode', False),            # Logs détaillés pour debugging
    )
    
    def __init__(self):
        super().__init__()
        
        # ═══════════════════════════════════════════════════════════════
        # INDICATEURS TECHNIQUES
        # ═══════════════════════════════════════════════════════════════
        
        # Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )
        
        # Keltner Channels
        self.keltner = KeltnerChannels(
            self.data,
            period=self.params.keltner_period,
            atr_period=self.params.keltner_period,
            multiplier=self.params.keltner_mult
        )
        
        # ATR
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # ATR SMA (pour comparaison)
        self.atr_sma = bt.indicators.SMA(
            self.atr,
            period=self.params.min_squeeze_days
        )
        
        # Volume
        self.volume_sma = bt.indicators.SMA(
            self.data.volume,
            period=self.params.volume_period
        )
        
        # ADX
        self.adx = bt.indicators.ADX(
            self.data,
            period=self.params.adx_period
        )
        
        # SMA 200 (tendance long terme)
        self.sma_200 = bt.indicators.SMA(
            self.data.close,
            period=self.params.sma_long_period
        )
        
        # RSI
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        
        # ═══════════════════════════════════════════════════════════════
        # VARIABLES DE SUIVI DU SQUEEZE (CORRIGÉES)
        # ═══════════════════════════════════════════════════════════════
        
        self.squeeze_days = 0               # Compteur jours de squeeze actuel
        self.in_squeeze = False             # État du squeeze actuel
        
        # ✅ NOUVEAU: Conserver info du dernier squeeze valide
        self.last_valid_squeeze_days = 0    # Durée du dernier squeeze valide
        self.last_squeeze_height = 0        # Hauteur du dernier squeeze
        self.last_squeeze_end_date = None   # Date de fin du dernier squeeze
        self.squeeze_adx_history = []       # Historique ADX durant squeeze
        self.squeeze_volume_history = []    # Historique volume durant squeeze
        self.squeeze_atr_history = []       # Historique ATR durant squeeze
        
        # ═══════════════════════════════════════════════════════════════
        # VARIABLES DE POSITION
        # ═══════════════════════════════════════════════════════════════
        
        self.entry_price = 0                # Prix d'entrée
        self.stop_loss = 0                  # Stop loss
        self.target_price = 0               # Prix target
        self.trailing_stop = 0              # Trailing stop dynamique
        self.trailing_stop_active = False   # Trailing stop activé
        self.entry_date = None              # Date d'entrée
        
        # ═══════════════════════════════════════════════════════════════
        # STATISTIQUES
        # ═══════════════════════════════════════════════════════════════
        
        self.squeeze_count = 0              # Nombre de squeezes détectés
        self.valid_squeeze_count = 0        # Nombre de squeezes valides
        self.breakout_attempts = 0          # Tentatives de breakout
        self.successful_entries = 0         # Entrées réussies
        
        self.log(
            f"\n{'='*70}\n"
            f"SqueezeMomentum V2 INITIALISÉE\n"
            f"{'='*70}\n"
            f"Indicateurs:\n"
            f"  - Bollinger Bands: {self.params.bb_period} périodes, {self.params.bb_std} std\n"
            f"  - Keltner Channels: {self.params.keltner_period} périodes, {self.params.keltner_mult}× ATR\n"
            f"  - ADX: {self.params.adx_period} périodes\n"
            f"  - SMA Long: {self.params.sma_long_period} périodes\n"
            f"  - RSI: {self.params.rsi_period} périodes\n"
            f"\n"
            f"Conditions Squeeze:\n"
            f"  - Durée minimum: {self.params.min_squeeze_days} jours\n"
            f"  - ADX max: {self.params.squeeze_adx_max}\n"
            f"  - Volume factor: {self.params.squeeze_volume_factor}\n"
            f"\n"
            f"Conditions Breakout:\n"
            f"  - Volume multiplier: {self.params.breakout_volume_mult}×\n"
            f"  - ADX minimum: {self.params.breakout_adx_min}\n"
            f"  - ADX croissant: {self.params.require_adx_rising}\n"
            f"\n"
            f"Filtres Marché:\n"
            f"  - Tendance LT (SMA 200): {self.params.use_trend_filter}\n"
            f"  - RSI filter: {self.params.use_rsi_filter} (max: {self.params.rsi_max})\n"
            f"\n"
            f"Gestion Position:\n"
            f"  - Risque par trade: {self.params.risk_per_trade*100}%\n"
            f"  - Target: {self.params.target_multiplier}× squeeze height\n"
            f"  - Trailing stop: {self.params.use_trailing_stop}\n"
            f"{'='*70}\n"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # DÉTECTION DU SQUEEZE (CORRIGÉE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def is_squeeze_active(self):
        """
        Vérifie si un squeeze est actif
        
        Squeeze = Bollinger Bands complètement à l'intérieur des Keltner Channels
        
        Returns:
            bool: True si squeeze actif
        """
        bb_upper = self.bollinger.lines.top[0]
        bb_lower = self.bollinger.lines.bot[0]
        kc_upper = self.keltner.lines.top[0]
        kc_lower = self.keltner.lines.bot[0]
        
        # Squeeze actif si Bollinger complètement à l'intérieur de Keltner
        squeeze = (bb_upper <= kc_upper) and (bb_lower >= kc_lower)
        
        return squeeze
    
    def validate_squeeze_quality(self):
        """
        ✅ NOUVELLE FONCTION: Valide la qualité du squeeze en cours
        
        Vérifie que durant le squeeze:
        - ADX reste bas (< 25)
        - Volume reste faible
        - ATR reste contracté
        
        Returns:
            bool: True si squeeze de bonne qualité
        """
        if len(self.squeeze_adx_history) == 0:
            return False
        
        # 1. ADX moyen durant squeeze doit être < 25
        avg_adx = sum(self.squeeze_adx_history) / len(self.squeeze_adx_history)
        if avg_adx >= self.params.squeeze_adx_max:
            if self.params.debug_mode:
                self.log(
                    f"Squeeze invalide: ADX moyen {avg_adx:.2f} >= {self.params.squeeze_adx_max}",
                    level="DEBUG"
                )
            return False
        
        # 2. Volume moyen durant squeeze doit être < 90% de la SMA
        avg_volume_ratio = sum(self.squeeze_volume_history) / len(self.squeeze_volume_history)
        if avg_volume_ratio >= self.params.squeeze_volume_factor:
            if self.params.debug_mode:
                self.log(
                    f"Squeeze invalide: Volume moyen {avg_volume_ratio:.2f} >= {self.params.squeeze_volume_factor}",
                    level="DEBUG"
                )
            return False
        
        # 3. ATR moyen durant squeeze doit être contracté
        if len(self.squeeze_atr_history) > 0:
            avg_atr_ratio = sum(self.squeeze_atr_history) / len(self.squeeze_atr_history)
            if avg_atr_ratio >= self.params.squeeze_atr_factor:
                if self.params.debug_mode:
                    self.log(
                        f"Squeeze invalide: ATR moyen {avg_atr_ratio:.2f} >= {self.params.squeeze_atr_factor}",
                        level="DEBUG"
                    )
                return False
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # DÉTECTION DU BREAKOUT (CORRIGÉE ET AMÉLIORÉE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def check_market_context(self):
        """
        ✅ NOUVELLE FONCTION: Vérifie le contexte marché avant d'entrer
        
        Returns:
            tuple: (bool, str) - (valide, raison si invalide)
        """
        # 1. FILTRE TENDANCE LONG TERME
        if self.params.use_trend_filter:
            if self.data.close[0] < self.sma_200[0]:
                return False, f"Prix sous SMA 200 ({self.data.close[0]:.2f} < {self.sma_200[0]:.2f})"
        
        # 2. FILTRE RSI (éviter surachat extrême)
        if self.params.use_rsi_filter:
            if self.rsi[0] > self.params.rsi_max:
                return False, f"RSI surachat ({self.rsi[0]:.2f} > {self.params.rsi_max})"
        
        # # 3. FILTRE PRIX MINIMUM
        # if self.data.close[0] < self.params.min_price:
        #     return False, f"Prix trop bas ({self.data.close[0]:.2f} < {self.params.min_price})"
        
        return True, ""
    
    def check_breakout_conditions(self):
        """
        ✅ FONCTION CORRIGÉE: Vérifie les conditions de breakout LONG
        
        Returns:
            tuple: (bool, str) - (valide, raison détaillée)
        """
        close = self.data.close[0]
        open_price = self.data.open[0]
        bb_upper = self.bollinger.lines.top[0]
        
        # ═══════════════════════════════════════════════════════════════
        # 1. PRIX: Bougie haussière qui clôture AU-DESSUS de BB upper
        # ═══════════════════════════════════════════════════════════════
        
        if close <= bb_upper:
            return False, f"Prix ne dépasse pas BB Upper ({close:.2f} <= {bb_upper:.2f})"
        
        if close <= open_price:
            return False, "Bougie baissière"
        
        # Vérifier que la bougie a un corps significatif (pas un doji)
        candle_range = self.data.high[0] - self.data.low[0]
        candle_body = abs(close - open_price)
        if candle_range > 0:
            body_pct = candle_body / candle_range
            if body_pct < self.params.min_candle_body_pct:
                return False, f"Corps de bougie trop petit ({body_pct*100:.1f}% < {self.params.min_candle_body_pct*100:.1f}%)"
        
        # ═══════════════════════════════════════════════════════════════
        # 2. VOLUME: Explosif (>2× moyenne)
        # ═══════════════════════════════════════════════════════════════
        
        volume_ratio = self.data.volume[0] / self.volume_sma[0]
        if volume_ratio < self.params.breakout_volume_mult:
            return False, f"Volume insuffisant ({volume_ratio:.2f}× < {self.params.breakout_volume_mult}×)"
        
        # ═══════════════════════════════════════════════════════════════
        # 3. ADX: Montre une vraie tendance (>20)
        # ═══════════════════════════════════════════════════════════════
        
        if self.adx[0] < self.params.breakout_adx_min:
            return False, f"ADX trop bas ({self.adx[0]:.2f} < {self.params.breakout_adx_min})"
        
        # ✅ NOUVEAU: ADX doit être CROISSANT (momentum)
        if self.params.require_adx_rising:
            if self.adx[0] <= self.adx[-1]:
                return False, f"ADX non croissant ({self.adx[0]:.2f} <= {self.adx[-1]:.2f})"
        
        # ═══════════════════════════════════════════════════════════════
        # 4. CONTEXTE MARCHÉ
        # ═══════════════════════════════════════════════════════════════
        
        context_valid, context_reason = self.check_market_context()
        if not context_valid:
            return False, f"Contexte marché: {context_reason}"
        
        # ✅ TOUS LES CRITÈRES VALIDÉS
        return True, "Breakout valide"
    
    # ═══════════════════════════════════════════════════════════════════════
    # GESTION DES POSITIONS (AMÉLIORÉE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def calculate_position_size(self, entry_price, stop_loss):
        """
        ✅ FONCTION AMÉLIORÉE: Calcule la taille de position
        
        Basé sur:
        - 2% de risque par trade
        - Maximum 20% du capital par position
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Prix du stop loss
        
        Returns:
            int: Nombre d'actions à acheter
        """
        portfolio_value = self.broker.getvalue()
        risk_amount = portfolio_value * self.params.risk_per_trade
        risk_per_share = entry_price - stop_loss
        
        if risk_per_share <= 0:
            self.log(
                f"⚠️  Erreur: stop_loss ({stop_loss:.2f}) >= entry_price ({entry_price:.2f})",
                level="ERROR"
            )
            return 0
        
        # Taille basée sur le risque
        size_by_risk = int(risk_amount / risk_per_share)
        
        # ✅ NOUVEAU: Limiter à max_position_pct du capital
        max_size_by_capital = int(
            (portfolio_value * self.params.max_position_pct) / entry_price
        )
        
        size = min(size_by_risk, max_size_by_capital)
        
        # Vérifier capital disponible
        required_capital = size * entry_price
        available_cash = self.broker.getcash()
        
        if required_capital > available_cash:
            size = int(available_cash / entry_price)
            self.log(
                f"⚠️  Capital insuffisant. Taille ajustée: {size}",
                level="WARNING"
            )
        
        return max(size, 0)
    
    def update_trailing_stop(self):
        """
        ✅ NOUVELLE FONCTION: Met à jour le trailing stop intelligemment
        
        Le trailing stop s'active après que le prix ait bougé
        de 1.5× la hauteur du squeeze
        """
        if not self.position or not self.params.use_trailing_stop:
            return
        
        current_price = self.data.close[0]
        profit = current_price - self.entry_price
        
        # Activer le trailing stop après 1.5× squeeze height de profit
        activation_threshold = self.last_squeeze_height * self.params.trailing_stop_activation
        
        if not self.trailing_stop_active:
            if profit >= activation_threshold:
                self.trailing_stop_active = True
                self.log(
                    f"✅ Trailing stop ACTIVÉ @ {current_price:.2f} "
                    f"(profit: ${profit:.2f}, seuil: ${activation_threshold:.2f})"
                )
        
        # Si trailing stop actif, suivre la Bollinger Lower Band
        if self.trailing_stop_active:
            bb_lower = self.bollinger.lines.bot[0]
            if bb_lower > self.trailing_stop:
                old_trailing = self.trailing_stop
                self.trailing_stop = bb_lower
                self.log(
                    f"📈 Trailing stop rehaussé: ${old_trailing:.2f} → ${self.trailing_stop:.2f}"
                )
    
    def check_exit_conditions(self):
        """
        ✅ FONCTION AMÉLIORÉE: Vérifie les conditions de sortie
        
        Returns:
            tuple: (bool, str) - (sortir, raison)
        """
        if not self.position:
            return False, ""
        
        current_price = self.data.close[0]
        
        # ═══════════════════════════════════════════════════════════════
        # 1. STOP LOSS (bande moyenne Bollinger)
        # ═══════════════════════════════════════════════════════════════
        
        if current_price <= self.stop_loss:
            return True, f"STOP LOSS @ ${current_price:.2f} (SL: ${self.stop_loss:.2f})"
        
        # ═══════════════════════════════════════════════════════════════
        # 2. TARGET ATTEINT
        # ═══════════════════════════════════════════════════════════════
        
        if current_price >= self.target_price:
            return True, f"TARGET atteint @ ${current_price:.2f} (Target: ${self.target_price:.2f})"
        
        # ═══════════════════════════════════════════════════════════════
        # 3. TRAILING STOP (si activé)
        # ═══════════════════════════════════════════════════════════════
        
        if self.trailing_stop_active and current_price <= self.trailing_stop:
            return True, f"TRAILING STOP @ ${current_price:.2f} (Trailing: ${self.trailing_stop:.2f})"
        
        # ═══════════════════════════════════════════════════════════════
        # 4. RETOUR DANS LE SQUEEZE (signal inverse)
        # ═══════════════════════════════════════════════════════════════
        
        if self.is_squeeze_active():
            return True, f"SIGNAL INVERSE - Retour dans squeeze @ ${current_price:.2f}"
        
        # ═══════════════════════════════════════════════════════════════
        # 5. ADX CHUTE (perte de momentum)
        # ═══════════════════════════════════════════════════════════════
        
        if self.adx[0] < self.params.breakout_adx_min * 0.7:  # ADX tombe sous 70% du minimum
            return True, f"PERTE MOMENTUM - ADX chute @ {self.adx[0]:.2f}"
        
        return False, ""
    
    # ═══════════════════════════════════════════════════════════════════════
    # LOGIQUE PRINCIPALE (CORRIGÉE)
    # ═══════════════════════════════════════════════════════════════════════
    
    def next(self):
        """✅ LOGIQUE PRINCIPALE CORRIGÉE"""
        
        # ═══════════════════════════════════════════════════════════════
        # VÉRIFICATIONS PRÉLIMINAIRES
        # ═══════════════════════════════════════════════════════════════
        
        # Attendre d'avoir assez de données
        if len(self.data) < max(
            self.params.volume_period,
            self.params.sma_long_period,
            self.params.bb_period
        ):
            return
        
        # Filtre liquidité minimum
        if self.params.use_min_volume_ratio :
            if self.data.volume[0] < self.volume_sma[0] * self.params.min_volume_ratio:
                return
        
        # ═══════════════════════════════════════════════════════════════
        # GESTION DES POSITIONS OUVERTES
        # ═══════════════════════════════════════════════════════════════
        
        if self.position:
            # Mise à jour du trailing stop
            self.update_trailing_stop()
            
            # Vérifier conditions de sortie
            should_exit, exit_reason = self.check_exit_conditions()
            
            if should_exit:
                if not self.order:
                    self.log(
                        f"\n{'='*70}\n"
                        f"🚪 SIGNAL DE SORTIE\n"
                        f"{'='*70}\n"
                        f"Raison:          {exit_reason}\n"
                        f"Prix sortie:     ${self.data.close[0]:.2f}\n"
                        f"Prix entrée:     ${self.entry_price:.2f}\n"
                        f"P&L estimé:      ${(self.data.close[0] - self.entry_price) * self.position.size:.2f}\n"
                        f"{'='*70}"
                    )
                    self.order = self.sell(size=self.position.size)
                    
                    # Réinitialiser les variables
                    self.entry_price = 0
                    self.stop_loss = 0
                    self.target_price = 0
                    self.trailing_stop = 0
                    self.trailing_stop_active = False
                    self.entry_date = None
            
            return
        
        # ═══════════════════════════════════════════════════════════════
        # DÉTECTION ET SUIVI DU SQUEEZE
        # ═══════════════════════════════════════════════════════════════
        
        if self.is_squeeze_active():
            if not self.in_squeeze:
                # ✅ DÉBUT D'UN NOUVEAU SQUEEZE
                self.in_squeeze = True
                self.squeeze_days = 1
                self.squeeze_count += 1
                
                # Réinitialiser les historiques
                self.squeeze_adx_history = [self.adx[0]]
                self.squeeze_volume_history = [self.data.volume[0] / self.volume_sma[0]]
                self.squeeze_atr_history = [self.atr[0] / self.atr_sma[0]]
                
                self.log(
                    f"🔒 SQUEEZE #{self.squeeze_count} détecté - Jour 1 "
                    f"(ADX: {self.adx[0]:.2f}, Vol: {self.data.volume[0]/self.volume_sma[0]:.2f}×)",
                    level="WARNING"
                )
            else:
                # ✅ SQUEEZE EN COURS
                self.squeeze_days += 1
                
                # Enregistrer les métriques
                self.squeeze_adx_history.append(self.adx[0])
                self.squeeze_volume_history.append(self.data.volume[0] / self.volume_sma[0])
                self.squeeze_atr_history.append(self.atr[0] / self.atr_sma[0])
                
                if self.squeeze_days == self.params.min_squeeze_days:
                    self.log(
                        f"✅ SQUEEZE #{self.squeeze_count} atteint {self.squeeze_days} jours "
                        f"(ADX moy: {sum(self.squeeze_adx_history)/len(self.squeeze_adx_history):.2f})",
                        level="WARNING"
                    )
                
                if self.params.debug_mode and self.squeeze_days % 2 == 0:
                    self.log(
                        f"🔒 Squeeze jour {self.squeeze_days} "
                        f"(ADX: {self.adx[0]:.2f}, Vol: {self.data.volume[0]/self.volume_sma[0]:.2f}×)",
                        level="DEBUG"
                    )
        else:
            # ✅ PAS DE SQUEEZE OU SQUEEZE TERMINÉ
            if self.in_squeeze:
                # ✅ FIN DU SQUEEZE - CONSERVER LES DONNÉES
                if self.squeeze_days >= self.params.min_squeeze_days:
                    # Valider la qualité du squeeze
                    if self.validate_squeeze_quality():
                        self.last_valid_squeeze_days = self.squeeze_days
                        self.last_squeeze_height = (
                            self.bollinger.lines.top[0] - self.bollinger.lines.bot[0]
                        )
                        self.last_squeeze_end_date = self.data.datetime.date(0)
                        self.valid_squeeze_count += 1
                        
                        self.log(
                            f"✅ SQUEEZE #{self.squeeze_count} VALIDE terminé après {self.squeeze_days} jours "
                            f"(Height: ${self.last_squeeze_height:.2f})",
                            level="WARNING"
                        )
                    else:
                        self.log(
                            f"❌ Squeeze #{self.squeeze_count} invalide (qualité insuffisante)",
                            level="WARNING"
                        )
                        self.last_valid_squeeze_days = 0
                else:
                    self.log(
                        f"❌ Squeeze #{self.squeeze_count} trop court ({self.squeeze_days} jours < {self.params.min_squeeze_days})"
                    )
                
                # Réinitialiser l'état du squeeze
                self.in_squeeze = False
                self.squeeze_days = 0
        
        # ═══════════════════════════════════════════════════════════════
        # RECHERCHE D'ENTRÉE (BREAKOUT)
        # ═══════════════════════════════════════════════════════════════
        
        if not self.order and not self.position:
            # ✅ VÉRIFIER QU'UN SQUEEZE VALIDE A EU LIEU RÉCEMMENT
            if self.last_valid_squeeze_days < self.params.min_squeeze_days:
                return
            
            # Vérifier que le squeeze n'est pas trop ancien (optionnel)
            # On peut trader le breakout jusqu'à 3 jours après la fin du squeeze
            if self.last_squeeze_end_date:
                days_since_squeeze = (
                    self.data.datetime.date(0) - self.last_squeeze_end_date
                ).days
                if days_since_squeeze > 5:
                    if self.params.debug_mode:
                        self.log(
                            f"Squeeze trop ancien ({days_since_squeeze} jours)",
                            level="DEBUG"
                        )
                    return
            
            # ✅ VÉRIFIER LES CONDITIONS DE BREAKOUT
            self.breakout_attempts += 1
            breakout_valid, breakout_reason = self.check_breakout_conditions()
            
            if breakout_valid:
                # ═══════════════════════════════════════════════════════
                # ✅ BREAKOUT VALIDE - CALCULER LES NIVEAUX
                # ═══════════════════════════════════════════════════════
                
                # Prix d'entrée
                self.entry_price = self.data.close[0]
                self.entry_date = self.data.datetime.date(0)
                
                # Stop Loss = Bollinger Middle Band
                self.stop_loss = self.bollinger.lines.mid[0]
                
                # Target = Entry + (Squeeze Height × 2)
                self.target_price = self.entry_price + (
                    self.last_squeeze_height * self.params.target_multiplier
                )
                
                # Trailing stop initial = Bollinger Lower Band
                self.trailing_stop = self.bollinger.lines.bot[0]
                self.trailing_stop_active = False
                
                # Calculer la taille de position (2% de risque)
                size = self.calculate_position_size(
                    self.entry_price,
                    self.stop_loss
                )
                
                if size > 0:
                    risk_reward = (
                        (self.target_price - self.entry_price) / 
                        (self.entry_price - self.stop_loss)
                    )
                    
                    self.log(
                        f"\n{'='*70}\n"
                        f"🚀 BREAKOUT LONG DÉTECTÉ !\n"
                        f"{'='*70}\n"
                        f"Date:            {self.entry_date}\n"
                        f"Prix entrée:     ${self.entry_price:.2f}\n"
                        f"Stop Loss:       ${self.stop_loss:.2f} ({((self.entry_price - self.stop_loss) / self.entry_price * 100):.2f}%)\n"
                        f"Target:          ${self.target_price:.2f} ({((self.target_price - self.entry_price) / self.entry_price * 100):.2f}%)\n"
                        f"Risk/Reward:     1:{risk_reward:.2f}\n"
                        f"Trailing Stop:   ${self.trailing_stop:.2f}\n"
                        f"\n"
                        f"Squeeze Info:\n"
                        f"  - Durée:       {self.last_valid_squeeze_days} jours\n"
                        f"  - Hauteur:     ${self.last_squeeze_height:.2f}\n"
                        f"\n"
                        f"Métriques Breakout:\n"
                        f"  - Volume:      {self.data.volume[0]/self.volume_sma[0]:.2f}× moyenne\n"
                        f"  - ADX:         {self.adx[0]:.2f}\n"
                        f"  - RSI:         {self.rsi[0]:.2f}\n"
                        f"  - SMA 200:     ${self.sma_200[0]:.2f}\n"
                        f"\n"
                        f"Position:\n"
                        f"  - Taille:      {size} actions\n"
                        f"  - Valeur:      ${size * self.entry_price:.2f}\n"
                        f"  - Risque:      ${size * (self.entry_price - self.stop_loss):.2f} ({self.params.risk_per_trade*100:.1f}%)\n"
                        f"  - Profit pot.: ${size * (self.target_price - self.entry_price):.2f}\n"
                        f"\n"
                        f"Stats:\n"
                        f"  - Squeezes:    {self.valid_squeeze_count}/{self.squeeze_count}\n"
                        f"  - Breakouts:   {self.breakout_attempts}\n"
                        f"  - Entrées:     {self.successful_entries + 1}\n"
                        f"{'='*70}"
                    )
                    
                    self.order = self.buy(size=size)
                    self.successful_entries += 1
                    
                    # Réinitialiser le squeeze après entrée
                    self.last_valid_squeeze_days = 0
            else:
                # Breakout invalide
                if self.params.debug_mode:
                    self.log(
                        f"❌ Breakout rejeté: {breakout_reason}",
                        level="DEBUG"
                    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def notify_order(self, order):
        """Notification des ordres"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"✅ ACHAT EXÉCUTÉ @ ${order.executed.price:.2f}, "
                    f"Taille: {order.executed.size}, "
                    f"Coût: ${order.executed.value:.2f}, "
                    f"Commission: ${order.executed.comm:.2f}"
                )
            else:
                profit = order.executed.price - self.entry_price if self.entry_price else 0
                profit_pct = (profit / self.entry_price * 100) if self.entry_price else 0
                
                self.log(
                    f"✅ VENTE EXÉCUTÉE @ ${order.executed.price:.2f}, "
                    f"Taille: {order.executed.size}, "
                    f"P&L: ${profit * order.executed.size:.2f} ({profit_pct:+.2f}%), "
                    f"Commission: ${order.executed.comm:.2f}"
                )
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('⚠️  Ordre annulé/rejeté', level="WARNING")
        
        self.order = None
    
    def notify_trade(self, trade):
        """Notification des trades fermés"""
        if not trade.isclosed:
            return
        
        # Calculer les statistiques du trade
        days_in_trade = (
            self.data.datetime.date(0) - self.entry_date
        ).days if self.entry_date else 0
        if trade.price * trade.size!= 0:
            self.log(
                f"\n{'='*70}\n"
                f"💰 TRADE FERMÉ\n"
                f"{'='*70}\n"
                f"Durée:        {days_in_trade} jours\n"
                f"Profit Brut:  ${trade.pnl:.2f}\n"
                f"Profit Net:   ${trade.pnlcomm:.2f}\n"
                f"Commission:   ${trade.commission:.2f}\n"
                f"ROI:          {(trade.pnl / (trade.price * trade.size) * 100):+.2f}%\n"
                f"{'='*70}\n"
            )
    
    def stop(self):
        """Appelé à la fin du backtest"""
        conversion_rate = (
            (self.successful_entries / self.breakout_attempts * 100) 
            if self.breakout_attempts > 0 else 0
        )
        
        self.log(
            f"\n{'='*70}\n"
            f"📊 STATISTIQUES FINALES\n"
            f"{'='*70}\n"
            f"Squeezes détectés:     {self.squeeze_count}\n"
            # f"Squeezes valides:      {self.valid_squeeze_count} ({self.valid_squeeze_count/self.squeeze_count*100:.1f}%)\n"
            f"Tentatives breakout:   {self.breakout_attempts}\n"
            f"Entrées réussies:      {self.successful_entries}\n"
            f"Taux de conversion:    {conversion_rate:.1f}%\n"
            f"Valeur finale:         ${self.broker.getvalue():.2f}\n"
            f"{'='*70}\n"
        )