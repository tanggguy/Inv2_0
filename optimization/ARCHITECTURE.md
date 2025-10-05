# 🏗️ Architecture du Nouveau Système d'Optimisation

## 📐 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    POINT D'ENTRÉE                               │
│                                                                 │
│                      optimize.py                                │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │   quick_start.py      │  Interface Interactive  │
│              └───────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODULE OPTIMIZATION                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   config.py  │  │ optimizer.py │  │ results_storage.py   │ │
│  │              │  │              │  │                      │ │
│  │ • Presets    │  │ • Grid Search│  │ • Historique        │ │
│  │ • Validation │  │ • Walk-Forward│ │ • Comparaisons     │ │
│  │ • Custom     │  │ • Progress   │  │ • Statistiques      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CONFIGURATION                               │
│                                                                 │
│               config/optimization_presets.json                  │
│                                                                 │
│  ┌─────────┐ ┌──────────┐ ┌────────────┐ ┌─────────────────┐ │
│  │  quick  │ │ standard │ │ exhaustive │ │  walk_forward   │ │
│  └─────────┘ └──────────┘ └────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STOCKAGE DES RÉSULTATS                       │
│                                                                 │
│                        results/                                 │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  history/optimization_runs.json                        │   │
│  │  • Index de tous les runs                             │   │
│  │  • Métadonnées rapides                                │   │
│  │  • Filtres et recherche                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  details/{run_id}/                                     │   │
│  │    ├── config.json      (configuration utilisée)      │   │
│  │    ├── results.csv      (tous les résultats)          │   │
│  │    └── summary.json     (résumé et meilleurs params)  │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux d'Exécution

### 1️⃣ Grid Search Flow

```
┌─────────────┐
│   START     │
└─────┬───────┘
      │
      ▼
┌─────────────────────────┐
│ Charger Configuration   │  ← load_preset('standard')
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Créer UnifiedOptimizer  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Générer Combinaisons    │  ← param_grid
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Pour chaque combo:      │
│  • Backtest             │
│  • Calculer métriques   │
│  • Stocker résultats    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Analyser Résultats      │
│  • Trier par Sharpe     │
│  • Identifier meilleur  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Sauvegarder             │
│  • history/index        │
│  • details/full_data    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────┐
│   DONE      │
└─────────────┘
```

### 2️⃣ Walk-Forward Flow

```
┌─────────────┐
│   START     │
└─────┬───────┘
      │
      ▼
┌─────────────────────────┐
│ Générer Périodes        │  ← in_sample + out_sample
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Pour chaque période:    │
│                         │
│  ┌───────────────────┐ │
│  │ In-Sample:        │ │
│  │  • Grid Search    │ │
│  │  • Find Best      │ │
│  └────────┬──────────┘ │
│           │            │
│           ▼            │
│  ┌───────────────────┐ │
│  │ Out-Sample:       │ │
│  │  • Test Best      │ │
│  │  • Measure Perf   │ │
│  └────────┬──────────┘ │
│           │            │
│           ▼            │
│  ┌───────────────────┐ │
│  │ Calculer          │ │
│  │  Dégradation      │ │
│  └───────────────────┘ │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Analyser Walk-Forward   │
│  • Avg degradation      │
│  • In vs Out Sharpe     │
│  • Robustesse           │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Sauvegarder + Rapport   │
└─────────┬───────────────┘
          │
          ▼
┌─────────────┐
│   DONE      │
└─────────────┘
```

---

## 🗂️ Structure des Données

### Config (Input)
```json
{
  "name": "standard",
  "description": "Configuration équilibrée",
  "symbols": ["AAPL", "MSFT"],
  "period": {
    "start": "2022-01-01",
    "end": "2024-01-01"
  },
  "capital": 100000,
  "param_grid": {
    "ma_period": [10, 20, 30, 50],
    "rsi_period": [7, 14, 21]
  }
}
```

### Results (Output)
```json
{
  "run_id": "opt_MaSuperStrategie_grid_20250104_143022",
  "best": {
    "sharpe": 2.34,
    "return": 45.2,
    "drawdown": -12.5,
    "ma_period": 20,
    "rsi_period": 14
  },
  "all_results": [
    {...},
    {...}
  ],
  "total_combinations": 12
}
```

### History Index
```json
{
  "runs": [
    {
      "run_id": "opt_MaSuperStrategie_grid_20250104_143022",
      "timestamp": "2025-01-04T14:30:22",
      "strategy": "MaSuperStrategie",
      "type": "grid_search",
      "best_sharpe": 2.34,
      "best_return": 45.2,
      "symbols": ["AAPL", "MSFT"],
      "period": {...}
    }
  ]
}
```

---

## 🔌 API Simplifiée

### Niveau 1: Ultra Simple
```python
from optimization.optimizer import optimize

results = optimize(strategy_class, preset_name='standard')
```

### Niveau 2: Configuration
```python
from optimization.config import load_preset
from optimization.optimizer import UnifiedOptimizer

config = load_preset('standard')
optimizer = UnifiedOptimizer(strategy_class, config)
results = optimizer.run()
```

### Niveau 3: Avancé
```python
from optimization.config import OptimizationConfig

config_manager = OptimizationConfig()
config = config_manager.create_custom(...)
optimizer = UnifiedOptimizer(strategy_class, config, 'walk_forward')

def progress(pct):
    print(f"{pct*100:.0f}%")

results = optimizer.run(progress_callback=progress)
```

### Niveau 4: Historique
```python
from optimization.results_storage import ResultsStorage

storage = ResultsStorage()
runs = storage.list_runs({'strategy': 'MaSuperStrategie'})
comparison = storage.compare_runs([id1, id2, id3])
best = storage.get_best_run(metric='sharpe')
```

---

## 📊 Comparaison Avant/Après

### Avant (4 fichiers isolés)

```
scripts/
├── optimize_strategy.py       ━━━┓
├── optimize_with_viz.py        ━━━┫ Code dupliqué
├── walk_forward_optimization.py━━━┫ Config hardcodée
└── optimize_my_strategy.py    ━━━┛ Pas d'historique

❌ Problèmes:
  • 4 points d'entrée différents
  • Code dupliqué (~60%)
  • Config hardcodée
  • Résultats perdus
  • Difficile à maintenir
```

### Après (Architecture unifiée)

```
optimization/
├── __init__.py
├── config.py          ━━━┓
├── optimizer.py       ━━━┫ Architecture modulaire
└── results_storage.py ━━━┛

config/
└── optimization_presets.json ━━━ Config centralisée

results/
├── history/           ━━━┓
└── details/           ━━━┛ Historique permanent

✅ Avantages:
  • 1 point d'entrée unifié
  • Code modulaire (0% duplication)
  • Config réutilisable
  • Historique complet
  • Facile à étendre
```

---

## 🎯 Points Clés de l'Architecture

### 1. Séparation des Responsabilités

```
config.py         → Gestion des configurations
optimizer.py      → Logique d'optimisation
results_storage.py→ Persistence des données
```

### 2. Configuration Centralisée

```
optimization_presets.json → Source unique de vérité
```

### 3. Historique Permanent

```
history/          → Index rapide
details/{run_id}/ → Données complètes
```

### 4. Extensibilité

```python
# Ajouter un nouveau type d'optimisation
class UnifiedOptimizer:
    def _bayesian_optimization(self):
        # Nouvelle méthode
        pass
```

### 5. Dashboard Ready

```
Toutes les données sont structurées 
pour être consommées par Streamlit
```

---

## 🚀 Prochaine Étape: Dashboard

```
dashboard/
├── app.py                    # Main Streamlit app
├── pages/
│   ├── 1_Run_Optimization.py
│   ├── 2_View_History.py
│   └── 3_Compare_Runs.py
└── components/
    ├── optimizer_form.py
    ├── results_table.py
    └── charts.py

→ Utilisera optimization/ comme backend
→ Interface graphique complète
→ Visualisations interactives
```

---

## ✅ Validation

### Tests Automatiques
```bash
python scripts/test_refactoring.py
```

Vérifie:
- ✅ Chargement configs
- ✅ Grid Search
- ✅ Walk-Forward
- ✅ Stockage
- ✅ Historique

### Test Manuel
```bash
python optimize.py
```

Doit permettre:
- ✅ Choisir stratégie
- ✅ Choisir preset
- ✅ Personnaliser
- ✅ Lancer optimisation
- ✅ Voir résultats

---

## 📈 Métriques de Succès

| Critère | Avant | Après |
|---------|-------|-------|
| **Lignes de code** | ~2000 | ~1500 |
| **Duplication** | ~60% | 0% |
| **Fichiers** | 4 | 3 |
| **Config** | Hardcodée | JSON |
| **Historique** | ❌ | ✅ |
| **Tests** | ❌ | ✅ |
| **Documentation** | ❌ | ✅ |
| **Dashboard Ready** | ❌ | ✅ |

---

**🎉 Architecture complète et validée ! Prêt pour le Dashboard Streamlit.**