# 📊 Guide Complet : Stratégie Squeeze Momentum V2

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Concepts Fondamentaux](#concepts-fondamentaux)
3. [Indicateurs Techniques Utilisés](#indicateurs-techniques-utilisés)
4. [Logique de la Stratégie](#logique-de-la-stratégie)
5. [Paramètres de Configuration](#paramètres-de-configuration)
6. [Gestion des Risques](#gestion-des-risques)
7. [Exemples Pratiques](#exemples-pratiques)
8. [Tickers Recommandés](#tickers-recommandés)
9. [Optimisation et Backtesting](#optimisation-et-backtesting)
10. [Erreurs Courantes à Éviter](#erreurs-courantes-à-éviter)

---

## 1. Vue d'Ensemble

### 🎯 Objectif de la Stratégie

La **Squeeze Momentum Strategy** est une stratégie de breakout qui vise à capturer les mouvements explosifs qui suivent des périodes de consolidation du marché. Elle combine analyse de volatilité, momentum et volume pour identifier les opportunités à haute probabilité.

### 📈 Type de Stratégie

- **Catégorie** : Breakout / Momentum
- **Direction** : Long uniquement (positions acheteuses)
- **Timeframe** : Daily (journalier)
- **Marchés** : Actions US, ETF tech
- **Complexité** : Avancée
- **Win Rate attendu** : 50-55%
- **Ratio Risque/Rendement** : 1:2 (minimum)

### ✅ Forces de la Stratégie

- ✅ Capture les mouvements importants après consolidation
- ✅ Multiples confirmations réduisent les faux signaux
- ✅ Gestion des risques intégrée (stop loss, trailing stop)
- ✅ Filtres de contexte marché pour améliorer le timing
- ✅ Adaptable à différents actifs liquides

### ⚠️ Limitations

- ⚠️ Nécessite de la patience (peu de signaux)
- ⚠️ Requiert une liquidité importante (volume élevé)
- ⚠️ Peut générer des faux breakouts
- ⚠️ Ne convient pas aux marchés très volatils ou en forte baisse

---

## 2. Concepts Fondamentaux

### 🔍 Qu'est-ce qu'un "Squeeze" ?

Un **squeeze** (compression) se produit lorsque :

1. **La volatilité se contracte** : Le prix oscille dans une fourchette de plus en plus étroite
2. **Le volume diminue** : Les traders attendent et n'agissent pas
3. **L'incertitude règne** : Le marché hésite entre hausse et baisse
4. **Une "pression" s'accumule** : Comme un ressort comprimé

#### Analogie Physique

```
Imaginez un ressort comprimé :
┌─────────┐
│ ▓▓▓▓▓▓▓ │  ← Ressort comprimé (squeeze)
└─────────┘

Puis relâché :
    ▓
    ▓
    ▓  ← Expansion explosive (breakout)
    ▓
┌─────────┐
```

### 📊 Squeeze vs Breakout

| Phase | Caractéristiques | Durée Typique |
|-------|------------------|---------------|
| **Squeeze** | Prix dans range étroit, volume faible, ADX bas | 5-15 jours |
| **Breakout** | Prix sort du range, volume explosif, ADX monte | 1-3 jours |
| **Expansion** | Tendance établie, momentum fort, volatilité élevée | 5-20 jours |

### 🎯 Pourquoi Cette Stratégie Fonctionne ?

**Principe psychologique** : Après une période de consolidation, les traders deviennent nerveux. Dès qu'un mouvement commence, ils :

1. **FOMO** (Fear Of Missing Out) : Peur de rater le mouvement
2. **Stops déclenchés** : Les positions perdantes sortent en masse
3. **Breakout alimenté** : Le mouvement s'auto-alimente
4. **Momentum créé** : La tendance s'établit

**Principe technique** : La volatilité est cyclique :
- Basse volatilité → Haute volatilité → Basse volatilité...
- La stratégie profite du passage de bas à haut

---

## 3. Indicateurs Techniques Utilisés

### 📐 1. Bollinger Bands (Bandes de Bollinger)

#### Définition

Les Bollinger Bands mesurent la volatilité du prix autour de sa moyenne mobile.

#### Formule

```
Ligne Médiane (MB) = SMA(20)
Bande Supérieure = SMA(20) + (2 × Écart-Type)
Bande Inférieure = SMA(20) - (2 × Écart-Type)
```

#### Paramètres

- **Période** : 20 jours
- **Multiplicateur** : 2.0 (écarts-types)

#### Interprétation

```
Prix
 ↑
 │     ╱──────╲        Bande Supérieure
 │    ╱        ╲       
 │───●──────────●───   Ligne Médiane (SMA 20)
 │    ╲        ╱       
 │     ╲──────╱        Bande Inférieure
 └────────────────→ Temps

Bandes LARGES = Haute volatilité
Bandes ÉTROITES = Basse volatilité (squeeze potentiel)
```

#### Rôle dans la Stratégie

1. **Détection du squeeze** : Quand les bandes se contractent
2. **Signal de breakout** : Prix casse la bande supérieure
3. **Stop loss** : Placé à la ligne médiane
4. **Trailing stop** : Suit la bande inférieure

---

### 📐 2. Keltner Channels (Canaux de Keltner)

#### Définition

Les Keltner Channels utilisent l'ATR (volatilité réelle) au lieu de l'écart-type.

#### Formule

```
Ligne Médiane = EMA(20)
Canal Supérieur = EMA(20) + (2 × ATR(20))
Canal Inférieur = EMA(20) - (2 × ATR(20))
```

#### Paramètres

- **Période EMA** : 20 jours
- **Période ATR** : 20 jours
- **Multiplicateur** : 2.0

#### Différence avec Bollinger

| Aspect | Bollinger Bands | Keltner Channels |
|--------|----------------|------------------|
| **Base** | Écart-type (volatilité statistique) | ATR (volatilité réelle) |
| **Sensibilité** | Plus réactif aux pics | Plus stable |
| **Usage** | Détection squeeze | Enveloppe de référence |

#### Rôle dans la Stratégie

**Le squeeze est confirmé quand** : Bollinger DANS Keltner

```
Squeeze détecté :
    Keltner ╱────────────╲
    │      ╱──╲          │  ← Bollinger à l'intérieur
    │      ╲──╱          │
    │    ╲────────────╱  │
    Keltner
```

---

### 📐 3. ATR (Average True Range)

#### Définition

L'ATR mesure la volatilité moyenne du prix sur une période donnée.

#### Formule

```
True Range (TR) = Max de :
  - High - Low
  - |High - Close précédent|
  - |Low - Close précédent|

ATR(14) = Moyenne mobile du TR sur 14 périodes
```

#### Paramètres

- **Période** : 14 jours

#### Interprétation

| ATR | Signification | Action |
|-----|---------------|--------|
| **Bas** | Marché calme, range | Attendre squeeze |
| **Normal** | Volatilité moyenne | Conditions optimales |
| **Élevé** | Marché agité | Réduire taille position |

#### Rôle dans la Stratégie

1. **Détection squeeze** : ATR doit être bas et décroissant
2. **Calcul du stop loss** : Stop = Entry - (2 × ATR)
3. **Position sizing** : Ajuster selon ATR actuel vs moyenne

#### Exemple

```
AAPL - Prix : 180$
ATR actuel : 3.50$
ATR moyen 50j : 4.00$

Ratio ATR = 3.50 / 4.00 = 0.875
→ Volatilité normale/basse ✓
→ Conditions favorables pour squeeze

Stop Loss calculé : 180 - (2 × 3.50) = 173$
→ Risque de -3.9% par trade
```

---

### 📐 4. ADX (Average Directional Index)

#### Définition

L'ADX mesure la **force** d'une tendance (pas sa direction).

#### Formule

```
ADX = SMA(14) de :
  DX = 100 × |+DI - -DI| / |+DI + -DI|

Où :
  +DI = Mouvement directionnel positif
  -DI = Mouvement directionnel négatif
```

#### Paramètres

- **Période** : 14 jours

#### Interprétation

| ADX | Type de Marché | Action |
|-----|----------------|--------|
| **< 20** | Pas de tendance, range | ✓ Conditions squeeze |
| **20-25** | Tendance faible | Zone de transition |
| **25-40** | Tendance forte | ✓ Conditions breakout |
| **> 40** | Tendance très forte | Suivre le mouvement |

#### Rôle dans la Stratégie

1. **Durant squeeze** : ADX < 25 (pas de tendance)
2. **Signal breakout** : ADX > 20 ET croissant
3. **Confirmation tendance** : ADX continue de monter après entrée

#### Exemple Visuel

```
ADX Evolution :

Squeeze Phase        Breakout        Expansion
    │                    │               │
 20 ├────────────────────┼───────────────┤
    │        ╱           │       ╱────   │
 15 ├───────╱            │    ╱──        │
    │    ╱──             │ ╱──           │
 10 ├─╱──                │               │
    └────────────────────┴───────────────┴→ Temps
    
    ADX < 20        ADX monte      ADX > 25
    (Range)         (Émergence)    (Tendance)
```

---

### 📐 5. Volume SMA (Moyenne Mobile du Volume)

#### Définition

Moyenne mobile simple du volume d'échanges quotidien.

#### Formule

```
Volume SMA(20) = Moyenne des volumes sur 20 derniers jours
```

#### Paramètres

- **Période** : 20 jours

#### Interprétation

| Ratio Volume/SMA | Signification | Trading |
|------------------|---------------|---------|
| **< 0.7** | Volume très faible | Éviter |
| **0.7 - 1.3** | Volume normal | OK |
| **> 1.5** | Volume élevé | Attention à confirmation |
| **> 2.0** | Volume explosif | ✓ Confirmation breakout |

#### Rôle dans la Stratégie

1. **Filtre liquidité** : Volume moyen > seuil minimum
2. **Durant squeeze** : Volume décroissant attendu
3. **Signal breakout** : Volume > 2× moyenne obligatoire
4. **Confirmation continuation** : Volume reste élevé

#### Exemple

```
NVDA - Analyse Volume

Jours Squeeze :
  Jour 1 : 35M actions (vs SMA 30M) = 1.17×
  Jour 3 : 28M actions = 0.93×
  Jour 5 : 22M actions = 0.73× ✓ Décroissant
  
Jour Breakout :
  Volume : 65M actions = 2.17× ✓ Explosif
  → Confirmation valide
```

---

### 📐 6. SMA 200 (Moyenne Mobile Simple 200 jours)

#### Définition

Moyenne du prix de clôture sur les 200 derniers jours de trading.

#### Formule

```
SMA(200) = Somme(Close sur 200j) / 200
```

#### Paramètres

- **Période** : 200 jours (environ 1 an de trading)

#### Interprétation

```
Prix > SMA 200 : Tendance long terme HAUSSIÈRE ✓
Prix < SMA 200 : Tendance long terme BAISSIÈRE ✗
```

#### Rôle dans la Stratégie

**Filtre de contexte marché** (optionnel, désactivé par défaut) :
- N'entrer en position que si prix > SMA 200
- Évite les trades contre la tendance dominante
- Améliore le taux de réussite dans les marchés haussiers

---

### 📐 7. RSI (Relative Strength Index)

#### Définition

L'RSI mesure la force du momentum en comparant les gains et pertes récents.

#### Formule

```
RSI = 100 - [100 / (1 + RS)]

Où RS = Moyenne des hausses / Moyenne des baisses
sur n périodes (typiquement 14)
```

#### Paramètres

- **Période** : 14 jours

#### Interprétation

| RSI | Zone | Signification |
|-----|------|---------------|
| **> 70** | Surachat | Momentum fort, attention retournement |
| **50-70** | Haussier | Momentum positif sain |
| **30-50** | Neutre | Pas de momentum clair |
| **< 30** | Survente | Momentum faible |

#### Rôle dans la Stratégie

**Filtre de surachat** (optionnel, désactivé par défaut) :
- N'entrer que si RSI < 75
- Évite d'acheter au sommet
- Réduit le risque de retournement immédiat

---

## 4. Logique de la Stratégie

### 🔄 Cycle Complet de Trading

```
┌─────────────────────────────────────────────────────────────┐
│                    CYCLE SQUEEZE MOMENTUM                    │
└─────────────────────────────────────────────────────────────┘

    1. FILTRAGE PRÉALABLE
       │
       ├─→ Volume minimum OK ? ───→ NON → SKIP
       │   OUI ↓
       │
       └─→ Liquide suffisant ? ───→ NON → SKIP
           OUI ↓

    2. DÉTECTION SQUEEZE
       │
       ├─→ Bollinger dans Keltner ? ──→ NON → ATTENDRE
       │   OUI ↓
       │
       ├─→ ADX < 25 ? ────────────────→ NON → PAS SQUEEZE
       │   OUI ↓
       │
       ├─→ Volume décroissant ? ──────→ NON → PAS SQUEEZE
       │   OUI ↓
       │
       └─→ Au moins 5 jours ? ────────→ NON → ATTENDRE
           OUI ↓

    3. ATTENTE BREAKOUT
       │
       └─→ Surveiller chaque jour

    4. DÉTECTION BREAKOUT
       │
       ├─→ Prix > Bollinger Upper ? ──→ NON → ATTENDRE
       │   OUI ↓
       │
       ├─→ Bougie haussière ? ────────→ NON → ATTENDRE
       │   OUI ↓
       │
       ├─→ Volume > 2× moyenne ? ─────→ NON → FAUX SIGNAL
       │   OUI ↓
       │
       ├─→ ADX > 20 ? ────────────────→ NON → ATTENDRE
       │   OUI ↓
       │
       └─→ ADX croissant ? ───────────→ NON → ATTENDRE
           OUI ↓

    5. ENTRÉE EN POSITION
       │
       ├─→ Calculer taille position (2% risque)
       ├─→ Définir Stop Loss (Bollinger Mid)
       ├─→ Définir Target (2× hauteur squeeze)
       └─→ Définir Trailing Stop

    6. GESTION POSITION
       │
       ├─→ Stop Loss touché ? ────────→ OUI → SORTIE (Perte)
       │   NON ↓
       │
       ├─→ Target atteint ? ──────────→ OUI → SORTIE (Gain)
       │   NON ↓
       │
       └─→ Trailing Stop touché ? ────→ OUI → SORTIE (Gain)
           NON → Continuer à surveiller
```

---

## 5. Paramètres de Configuration

### 📁 Fichier de Configuration

**Emplacement** : `config/strategies_config.yaml`

```yaml
squeeze_momentum:
  parameters:
    # Filtres préalables
    min_volume_avg: 1000000  # 1M actions/jour minimum
    
    # Périodes indicateurs
    bb_period: 20
    bb_std: 2.0
    keltner_period: 20
    keltner_mult: 2.0
    atr_period: 14
    volume_period: 20
    adx_period: 14
    
    # Conditions squeeze
    min_squeeze_days: 5      # Minimum 5 jours
    squeeze_adx_max: 25      # ADX < 25
    
    # Conditions breakout
    breakout_volume_mult: 2.0   # Volume > 2× moyenne
    breakout_adx_min: 20        # ADX > 20
    require_adx_rising: true    # ADX croissant
    
    # Gestion sorties
    target_multiplier: 2.0      # Target = 2× hauteur
    use_trailing_stop: true
    trailing_stop_activation: 1.5
    risk_per_trade: 0.02        # 2% risque
```

---

## 6. Gestion des Risques

### 💼 Règles de Money Management

#### Position Sizing

```python
Position Size = (Capital × Risk%) / (Entry - Stop Loss)

Exemple :
  Capital : 50,000$
  Risk : 2% = 1,000$
  Entry : 250$
  Stop : 242$
  Risk/Share : 8$
  
  Size : 1,000$ / 8$ = 125 actions
```

#### Types de Stops

1. **Stop Loss Initial** : Bollinger Middle Band
2. **Trailing Stop** : Suit Bollinger Lower Band
3. **Take Profit** : Entry + (2× hauteur squeeze)

---

## 7. Exemples Pratiques

### 📈 Trade NVDA Réussi

```
SQUEEZE (Jours 1-5)
  Prix range : 485$ - 502$
  ADX : 18 → 15
  Volume décroissant ✓

BREAKOUT (Jour 6)
  Prix : 510$ (> Bollinger 502$) ✓
  Volume : 78M (× 2.23 moyenne) ✓
  ADX : 21 et croissant ✓

ENTRÉE (Jour 7)
  Entry : 511$
  Stop : 495$ (-3.1%)
  Target : 545$ (+6.7%)
  Size : 31 actions

SORTIE
  Jour 11 : 549$ (+7.4%)
  Gain : +1,002$ (6.3% ROI)
```

---

## 8. Tickers Recommandés

### Top Choix

**Tier 1 (Débutants)** :
- AAPL, MSFT, QQQ, SPY

**Tier 2 (Intermédiaire)** :
- NVDA, GOOGL, META, AMD

**Tier 3 (Avancé)** :
- TSLA, COIN, PLTR

---

## 9. Optimisation et Backtesting

```bash
# Backtest simple
python main.py --strategy squeeze_momentum --symbols AAPL --period 2y --plot

# Optimisation
python optimization/quick_optimize.py
```

---

## 10. Erreurs Courantes à Éviter

❌ Entrer trop tôt (avant 5 jours squeeze)
❌ Ignorer le volume breakout
❌ Ne pas utiliser de stop loss
❌ Déplacer le stop loss
❌ Overtrading
❌ Trader durant earnings
❌ Ignorer contexte marché

---

## Conclusion

La stratégie **Squeeze Momentum** offre une approche systématique pour trader les breakouts. Avec discipline et patience, elle peut générer des rendements constants.

**Clés du succès** :
✅ Patience (attendre 5+ jours squeeze)
✅ Discipline (respecter tous les critères)
✅ Gestion risque (2% maximum par trade)
✅ Objectivité (suivre les signaux)

**Bon trading ! 🚀**