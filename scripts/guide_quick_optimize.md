# ⚡ Optuna Quick Reference - Aide-Mémoire

```
╔══════════════════════════════════════════════════════════════╗
║  🚀 OPTUNA - OPTIMISATION BAYÉSIENNE ULTRA-RAPIDE 🚀       ║
╚══════════════════════════════════════════════════════════════╝
```

## 🎯 Commandes Essentielles

### Lancer une Optimisation
```bash
python scripts/quick_optimize_optuna.py
```

### Tester l'Installation
```bash
python tests/test_quick_optimize_optuna.py
```

---

## 📊 Presets Disponibles

| Preset | Trials | Durée | Usage |
|--------|--------|-------|-------|
| **quick** | 50 | ~5 min | 🏃 Test rapide |
| **standard** | 100 | ~10 min | 📊 Quotidien |
| **deep** | 200 | ~20 min | 🔬 Approfondi |
| **ultra** | 500 | 1-2h | 🌙 Nuit |

---

## 🎮 Navigation Menu

```
┌─────────────────────────────────────────────┐
│  1. Stratégie    → RSI (3)                 │
│  2. Type         → Optuna (3) 🚀           │
│  3. Preset       → optuna_quick (1)        │
│  4. Custom       → Non (n)                  │
│  5. Confirmer    → Oui (o)                  │
│  6. ⏳ Wait      → [████████] 100%          │
│  7. 🏆 Results   → Sharpe + Importance      │
└─────────────────────────────────────────────┘
```

---

## 📈 Interprétation des Résultats

### Sharpe Ratio
```
> 2.5  → ⭐⭐⭐⭐⭐ EXCELLENT
> 2.0  → ⭐⭐⭐⭐ TRÈS BON
> 1.5  → ⭐⭐⭐ BON
> 1.0  → ⭐⭐ ACCEPTABLE
< 1.0  → ⭐ FAIBLE
```

### Importance des Paramètres
```
> 0.5  → 🔥 CRITIQUE - Focus ici
0.2-0.5 → ⚡ IMPORTANT
0.1-0.2 → 📊 MODÉRÉ
< 0.1  → 🌫️ SECONDAIRE
```

---

## 💡 Workflows Rapides

### 🏃 Test Express (5 min)
```
Stratégie → RSI
Type → Optuna (3)
Preset → quick (1)
Custom → n
```

### 📊 Optimisation Standard (10 min)
```
Stratégie → Votre stratégie
Type → Optuna (3)
Preset → standard (2)
Custom → n
```

### 🔬 Recherche Poussée (20 min)
```
Stratégie → Stratégie complexe
Type → Optuna (3)
Preset → deep (3)
Custom → o (augmenter trials à 300)
```

---

## 🎯 Décisions Rapides

### Quel Preset Choisir ?

```
┌───────────────────────────────────────────┐
│ Nouveau test ?     → quick                │
│ Usage quotidien ?  → standard             │
│ Stratégie complexe ? → deep               │
│ Avant de dormir ?  → ultra                │
└───────────────────────────────────────────┘
```

### Combien de Trials ?

```
Stratégie Simple (2-3 params)  → 50-100 trials
Stratégie Moyenne (4-5 params) → 100-200 trials
Stratégie Complexe (6+ params) → 200-500 trials
```

---

## 🔧 Raccourcis Clavier

```
Pendant la Sélection:
[Enter]        → Choix par défaut
[1-9]          → Sélection rapide
[o] ou [Enter] → Confirmer
[n]            → Annuler/Passer

Pendant l'Optimisation:
[Ctrl+C]       → Arrêter (sauvegarde partielle)
```

---

## 📊 Fichiers Générés

```
optimization/
├── optuna_plots/
│   ├── {run_id}_history.html     📈 Convergence
│   ├── {run_id}_importance.html  🔬 Importance
│   ├── {run_id}_parallel.html    🌐 Relations
│   └── {run_id}_slice.html       📊 Impact
├── optuna_studies/
│   └── optuna.db                 💾 Database
└── results/
    └── {run_id}.json             📄 Résultats
```

---

## ⚡ Tips Pro

### 🚀 Vitesse Maximale
```python
# Dans customize_config
Symboles: 1 seul
Période: 1 an max
Trials: 50-100
→ Résultat en 5-10 min
```

### 🎯 Précision Maximale
```python
# Dans customize_config
Symboles: 1-2
Période: 2-3 ans
Trials: 200-500
→ Résultat optimal
```

### 🧠 Insights Maximaux
```python
# Après optimisation
1. Ouvrir importance.html
2. Focus sur top 2-3 params
3. Noter les valeurs optimales
4. Tester manuellement autour
```

---

## 🔍 Commandes Debug

### Vérifier Installation
```bash
python -c "import optuna; print(optuna.__version__)"
```

### Lister Études Optuna
```bash
sqlite3 optimization/optuna_studies/optuna.db "SELECT name FROM studies;"
```

### Compter Trials
```bash
sqlite3 optimization/optuna_studies/optuna.db "SELECT COUNT(*) FROM trials;"
```

---

## 📞 Support Rapide

### Erreur Commune #1: Import Error
```bash
pip install optuna optuna-dashboard plotly
```

### Erreur Commune #2: No Trials Completed
```
→ Vérifier les données (yfinance)
→ Réduire la période de test
→ Simplifier param_grid
```

### Erreur Commune #3: Très Lent
```
→ Réduire trials (100 → 50)
→ Période plus courte (2 ans → 1 an)
→ 1 seul symbole
```

---

## 🎓 Ressources

### Documentation
```
GUIDE_DEMARRAGE_OPTUNA.md        → Guide complet
MODIFICATIONS_*.md                → Détails techniques
RESUME_INTEGRATION_OPTUNA.md     → Vue d'ensemble
```

### Liens Externes
```
https://optuna.readthedocs.io/   → Doc officielle
https://optuna.org/               → Site web
```

---

## 🏆 Best Practices

### ✅ DO
- Commencer avec quick (50 trials)
- Analyser l'importance des paramètres
- Itérer progressivement (quick → standard → deep)
- Sauvegarder les bons runs
- Consulter les visualisations

### ❌ DON'T
- Commencer avec ultra (500 trials)
- Ignorer l'importance des paramètres
- Tester 10 symboles en même temps
- Oublier de valider en Walk-Forward
- Négliger l'analyse des résultats

---

## 🎯 Objectifs par Niveau

### Débutant (Semaine 1)
```
□ Lancer première optimisation Optuna
□ Comprendre Sharpe Ratio
□ Lire importance des paramètres
□ Visualiser history.html
```

### Intermédiaire (Semaine 2-4)
```
□ Tester tous les presets
□ Comparer avec Grid Search
□ Optimiser 5+ stratégies
□ Analyser tous les graphiques
```

### Avancé (Mois 2+)
```
□ Créer presets personnalisés
□ Combiner avec Walk-Forward
□ Multi-objectif
□ Optimiser en production
```

---

## 📊 Checklist Quotidienne

```
Routine Optimisation (10 min/jour):

□ Lancer quick_optimize_optuna.py
□ Choisir stratégie du jour
□ Sélectionner Optuna (3)
□ Preset: standard (2)
□ Analyser Sharpe + Importance
□ Noter paramètres optimaux
□ Appliquer en production
```

---

## 🎨 Template Décision Rapide

```
┌────────────────────────────────────────────┐
│ BESOIN                  PRESET      DURÉE  │
├────────────────────────────────────────────┤
│ Test rapide        →   quick      5 min   │
│ Optimisation quotidienne → standard 10 min│
│ Recherche détaillée →   deep      20 min  │
│ Optimisation nuit  →   ultra     1-2h     │
└────────────────────────────────────────────┘
```

---

## 💰 ROI Temps

```
Grid Search:  4h  →  100% optimal
Optuna:      10m  →   98% optimal

Gain de temps: 96% ⚡
Perte qualité: 2% 📉
→ ROI: Excellent! 🎯
```

---

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  🎉 Vous êtes maintenant expert Optuna !                ║
║                                                          ║
║  Gardez cet aide-mémoire à portée de main               ║
║                                                          ║
║  Bon Trading ! 📈✨                                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

**Imprimez ce document et gardez-le sur votre bureau ! 📌**