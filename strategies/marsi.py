"""
MaRSI  - Version Améliorée
Stratégie de croisement MA avec RSI et filtres multiples

AMÉLIORATIONS:
- ✅ Correction bug double vente
- ✅ Ajout filtre de tendance EMA 200
- ✅ Ajout filtre de volume
- ✅ Paramètres RSI optimisés (14/30/70)
- ✅ Logging amélioré
- ✅ Validation de signaux renforcée
"""

from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt


class MaRSI(BaseAdvancedStrategy):
    """
    Stratégie MA Crossover + RSI avec filtres de qualité

    RÈGLES D'ENTRÉE (LONG):
    1. MA rapide croise au-dessus de MA lente (signal tendance)
    2. RSI < seuil survente (momentum favorable)
    3. Prix au-dessus EMA 200 (tendance long terme haussière)
    4. Volume supérieur à la moyenne (confirmation)

    RÈGLES DE SORTIE:
    1. Crossover baissier (inversion tendance)
    2. RSI en surachat (momentum excessif)
    3. Stop loss ATR (protection capital)
    4. Take profit / Trailing stop (sécurisation gains)
    """

    params = (
        # ========== INDICATEURS ==========
        ("fast_ma_period", 20),  # MA rapide (modifié de 50)
        ("slow_ma_period", 50),  # MA lente (modifié de 150)
        ("crossover_window", 5),  # Fenêtre
        ("rsi_period", 14),  # RSI standard (modifié de 7)
        ("rsi_oversold", 0),  # momentum chez les acheteurs, on suit la tendance
        ("rsi_overbought", 80),  # Vrai surachat (modifié de 65)
        ("ema_trend_period", 200),  #  Filtre tendance
        ("volume_sma_period", 20),  #  Moyenne volume
        ("volume_multiplier", 1.0),  #  Seuil volume
        # ========== FILTRES ==========
        ("use_trend_filter", True),  #  Activer filtre EMA 200
        ("use_volume_filter", True),  #  Activer filtre volume
        ("min_volume_ratio", 1.1),  #  Volume min / moyenne
        # ========== GESTION DES RISQUES ==========
        ("use_stop_loss", True),
        ("use_atr_stop", True),
        ("stop_loss_atr_mult", 2.0),
        ("atr_period", 14),
        ("use_take_profit", True),
        ("take_profit_pct", 0.05),  # take profit
        ("use_trailing_stop", True),
        ("trailing_stop_pct", 0.035),  # trailing
        ("trailing_activation_pct", 0.02),  # Active après x% de gain
        ("risk_per_trade", 0.02),  # Risque par trade
        ("max_position_pct", 0.20),  # Max du capital par position
        # ========== AUTRES ==========
        ("printlog", True),
    )

    def __init__(self):
        super().__init__()

        # ========== MOYENNES MOBILES ==========
        self.ma_fast = bt.indicators.SMA(
            self.datas[0].close, period=self.params.fast_ma_period
        )
        self.ma_slow = bt.indicators.SMA(
            self.datas[0].close, period=self.params.slow_ma_period
        )
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)

        # ========== RSI ==========
        self.rsi = bt.indicators.RSI(self.datas[0].close, period=self.params.rsi_period)

        # ========== FILTRE DE TENDANCE (EMA 200) ==========
        if self.params.use_trend_filter:
            self.ema_trend = bt.indicators.EMA(
                self.datas[0].close, period=self.params.ema_trend_period
            )

        # ========== FILTRE DE VOLUME ==========
        if self.params.use_volume_filter:
            self.volume_sma = bt.indicators.SMA(
                self.datas[0].volume, period=self.params.volume_sma_period
            )

        # ========== ATR POUR STOPS ==========
        self.atr = bt.indicators.ATR(period=self.params.atr_period)

        # ========== VARIABLES DE SUIVI ==========
        self.signal_count = 0
        self.filtered_signals = 0

        self.bars_since_crossover = 0
        self.last_crossover_direction = 0  # 1=haussier, -1=baissier, 0=aucun
        self.crossover_count = 0
        # Log de l'initialisation
        self.log("=" * 70)
        self.log("MaRSI ENHANCED - Stratégie initialisée")
        self.log("=" * 70)
        self.log(
            f"MA Rapide: {self.params.fast_ma_period} | MA Lente: {self.params.slow_ma_period}"
        )
        self.log(
            f"RSI: {self.params.rsi_period} (Survente: {self.params.rsi_oversold}, Surachat: {self.params.rsi_overbought})"
        )
        self.log(
            f"Filtres actifs: Tendance={self.params.use_trend_filter}, Volume={self.params.use_volume_filter}"
        )
        self.log(
            f"Gestion risque: Stop ATR {self.params.stop_loss_atr_mult}x, TP {self.params.take_profit_pct*100}%"
        )
        self.log("=" * 70)

    def calculate_position_size(self):
        """
        Calcule la taille de position basée sur l'ATR et le risque défini

        Formule: Taille = (Capital × %Risque) / (ATR × Multiplicateur)

        Returns:
            int: Nombre d'actions à acheter
        """
        if len(self.atr) < 1:
            self.log("⚠️  ATR insuffisant pour calculer position size")
            return 0

        # Capital disponible
        capital = self.broker.getvalue()

        # Montant à risquer sur ce trade
        risk_amount = capital * self.params.risk_per_trade

        # Distance du stop loss en points
        atr_value = self.atr[0]
        stop_distance = atr_value * self.params.stop_loss_atr_mult

        # Prix actuel
        current_price = self.datas[0].close[0]

        # Calcul de la taille de position
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            self.log("⚠️  Stop distance invalide")
            return 0

        # Taille maximale autorisée (en nombre d'actions)
        max_size = (capital * self.params.max_position_pct) / current_price

        # Prendre le minimum entre la taille calculée et la taille max
        final_size = min(position_size, max_size)

        # Arrondir à l'entier inférieur
        final_size = int(final_size)

        # Log détaillé
        self.log("┌─ CALCUL POSITION SIZE ─────────────────────")
        self.log(f"│ Capital: {capital:.2f} €")
        self.log(
            f"│ Risque par trade: {risk_amount:.2f} € ({self.params.risk_per_trade*100}%)"
        )
        self.log(f"│ ATR: {atr_value:.2f}")
        self.log(
            f"│ Stop distance: {stop_distance:.2f} ({self.params.stop_loss_atr_mult}x ATR)"
        )
        self.log(f"│ Prix actuel: {current_price:.2f}")
        self.log(f"│ Taille calculée: {position_size:.2f} actions")
        self.log(f"│ Taille max autorisée: {max_size:.2f} actions")
        self.log(f"│ ✅ TAILLE FINALE: {final_size} actions")
        self.log(
            f"│ Valeur position: {final_size * current_price:.2f} € ({(final_size * current_price / capital)*100:.1f}%)"
        )
        self.log("└────────────────────────────────────────────")

        return final_size

    def validate_entry_signal(self):
        """
        Valide tous les critères d'entrée avec logging détaillé

        Returns:
            bool: True si tous les critères sont validés
        """
        self.signal_count += 1

        # Prix actuel
        current_price = self.datas[0].close[0]

        self.log("┌─ VALIDATION SIGNAL D'ENTRÉE ───────────────")
        self.log(f"│ Signal #{self.signal_count}")

        # # ===== CRITÈRE 1: CROSSOVER =====
        # crossover_valid = self.crossover > 0
        # self.log(f"│ 1️⃣  Crossover MA: {'✅ VALID' if crossover_valid else '❌ INVALID'}")
        # self.log(f"│    MA Fast: {self.ma_fast[0]:.2f} | MA Slow: {self.ma_slow[0]:.2f}")

        # if not crossover_valid:
        #     self.log("└────────────────────────────────────────────")
        #     self.filtered_signals += 1
        #     return False

        # ===== CRITÈRE 2: RSI =====
        rsi_value = self.rsi[0]
        rsi_valid = rsi_value > self.params.rsi_oversold
        self.log(f"│   RSI Survente: {'✅ VALID' if rsi_valid else '❌ INVALID'}")
        self.log(f"│    RSI: {rsi_value:.2f} (seuil: {self.params.rsi_oversold})")

        if not rsi_valid:
            self.log("└────────────────────────────────────────────")
            self.filtered_signals += 1
            return False

        # ===== CRITÈRE 3: TENDANCE (EMA 200) =====
        if self.params.use_trend_filter:
            trend_valid = current_price > self.ema_trend[0]
            self.log(f"│Tendance EMA200: {'✅ VALID' if trend_valid else '❌ INVALID'}")
            self.log(
                f"│    Prix: {current_price:.2f} | EMA200: {self.ema_trend[0]:.2f}"
            )

            if not trend_valid:
                self.log("└────────────────────────────────────────────")
                self.filtered_signals += 1
                return False
        else:
            self.log(f"│Tendance EMA200: ⏭️  DÉSACTIVÉ")

        # ===== CRITÈRE 4: VOLUME =====
        if self.params.use_volume_filter:
            current_volume = self.datas[0].volume[0]
            avg_volume = self.volume_sma[0]
            volume_valid = current_volume > (avg_volume * self.params.min_volume_ratio)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            self.log(f"│  Volume: {'✅ VALID' if volume_valid else '❌ INVALID'}")
            self.log(f"│    Volume: {current_volume:.0f} | Moyenne: {avg_volume:.0f}")
            self.log(
                f"│    Ratio: {volume_ratio:.2f}x (min: {self.params.min_volume_ratio}x)"
            )

            if not volume_valid:
                self.log("└────────────────────────────────────────────")
                self.filtered_signals += 1
                return False
        else:
            self.log(f"│Volume: ⏭️  DÉSACTIVÉ")

        # ===== TOUS LES CRITÈRES VALIDÉS =====
        self.log("│")
        self.log("│ 🎯 TOUS LES CRITÈRES VALIDÉS - SIGNAL D'ACHAT CONFIRMÉ")
        self.log("└────────────────────────────────────────────")

        return True

    def next(self):
        """
        Logique principale exécutée à chaque barre
        """
        # ===== VÉRIFICATION DES STOPS =====
        # TOUJOURS en premier !
        if self._check_stops():
            return

        # Ne pas trader si ordre en cours
        if self.order:
            return
        # ✅ Détecter nouveau croisement
        if self.crossover > 0:
            self.last_crossover_direction = 1
            self.bars_since_crossover = 0
            self.crossover_count += 1
            self.log(
                f"🔔 CROSSOVER HAUSSIER détecté - Fenêtre active {self.params.crossover_window} barres"
            )

        elif self.crossover < 0:
            self.last_crossover_direction = -1
            self.bars_since_crossover = 0
            self.log(f"🔔 CROSSOVER BAISSIER détecté")

        # ✅ Incrémenter compteur si crossover actif
        if self.last_crossover_direction != 0:
            self.bars_since_crossover += 1
            if self.bars_since_crossover <= self.params.crossover_window:
                remaining = self.params.crossover_window - self.bars_since_crossover + 1
                self.log(
                    f"📅 Fenêtre active: Jour {self.bars_since_crossover}/{self.params.crossover_window} (reste {remaining} barres)"
                )

        current_price = self.datas[0].close[0]

        # ========== LOGIQUE D'ACHAT ==========
        if not self.position:
            bullish_alignment = self.ma_fast[0] > self.ma_slow[0]

            in_crossover_window = (
                self.last_crossover_direction == 1
                and self.bars_since_crossover <= self.params.crossover_window
            )
            # Vérifier crossover haussier
            if in_crossover_window:
                # Valider tous les critères
                if self.validate_entry_signal():
                    # Calculer la taille de position
                    size = self.calculate_position_size()

                    if size > 0:
                        self.log("🚀 ════════════════════════════════════════")
                        self.log(f"🚀 ORDRE D'ACHAT PASSÉ")
                        self.log(f"🚀 Prix: {current_price:.2f}")
                        self.log(f"🚀 Taille: {size} actions")
                        self.log(f"🚀 Valeur: {size * current_price:.2f} €")
                        self.log("🚀 ════════════════════════════════════════")

                        self.order = self.buy(size=size)
                    else:
                        self.log("⚠️  Position size = 0, pas d'achat")
            # ✅ Expiration de la fenêtre
            elif (
                self.last_crossover_direction == 1
                and self.bars_since_crossover > self.params.crossover_window
            ):
                if self.bars_since_crossover == self.params.crossover_window + 1:
                    self.log(f"⏰ Fenêtre expirée - Attente nouveau crossover")
                self.last_crossover_direction = 0
        # ========== LOGIQUE DE VENTE ==========
        else:
            # ✅ CORRECTION: Utiliser elif au lieu de if multiple
            # Signal de vente: MA rapide croise en-dessous
            if self.crossover < 0:
                self.log("🔴 ════════════════════════════════════════")
                self.log(f"🔴 SIGNAL VENTE (Crossover baissier)")
                self.log(f"🔴 Prix: {current_price:.2f}")
                self.log("🔴 ════════════════════════════════════════")
                self.order = self.sell(size=self.position.size)

            # Signal de vente: RSI en surachat
            elif self.rsi[0] > self.params.rsi_overbought:
                self.log("🔴 ════════════════════════════════════════")
                self.log(f"🔴 SIGNAL VENTE (RSI surachat: {self.rsi[0]:.2f})")
                self.log(f"🔴 Prix: {current_price:.2f}")
                self.log("🔴 ════════════════════════════════════════")
                self.order = self.sell(size=self.position.size)

    def notify_trade(self, trade):
        """
        Appelé quand un trade est fermé
        """
        if not trade.isclosed:
            return

        # Calculer les statistiques du trade
        pnl = trade.pnl
        pnl_pct = (trade.pnl / trade.price) * 100 if trade.price > 0 else 0

        # Log du résultat
        self.log("╔═══════════════════════════════════════════╗")
        if pnl > 0:
            self.log("║       ✅ TRADE GAGNANT                    ║")
        else:
            self.log("║       ❌ TRADE PERDANT                    ║")
        self.log("╠═══════════════════════════════════════════╣")
        self.log(f"║ P&L Brut: {pnl:.2f} € ({pnl_pct:+.2f}%)       ║")
        self.log(f"║ P&L Net: {trade.pnlcomm:.2f} €              ║")
        self.log(f"║ Commission: {trade.commission:.2f} €        ║")
        self.log("╚═══════════════════════════════════════════╝")

    def stop(self):
        """
        Appelé à la fin du backtest
        """
        self.log("")
        self.log("╔═══════════════════════════════════════════════════╗")
        self.log("║          RÉSUMÉ DE LA STRATÉGIE                   ║")
        self.log("╠═══════════════════════════════════════════════════╣")
        self.log(f"║ Capital Final: {self.broker.getvalue():.2f} €")
        self.log(f"║ Signaux Totaux: {self.signal_count}")
        self.log(f"║ Signaux Filtrés: {self.filtered_signals}")
        self.log(
            f"║ Taux de Filtrage: {(self.filtered_signals/self.signal_count*100) if self.signal_count > 0 else 0:.1f}%"
        )
        self.log("╚═══════════════════════════════════════════════════╝")
