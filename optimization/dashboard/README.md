# 📊 Trading System Dashboard

Dashboard interactif Streamlit pour l'optimisation et l'analyse de stratégies de trading algorithmique.

## 🚀 Fonctionnalités

### 1. 🚀 Run Optimization
- Lancer des optimisations Grid Search ou Walk-Forward
- Sélection intuitive de stratégie et configuration
- Personnalisation des paramètres (symboles, période, capital)
- **Barre de progression en temps réel**
- Affichage immédiat des résultats
- Copie facile des meilleurs paramètres

### 2. 📋 View History
- **Tableau filtrable et triable** de tous les runs
- Filtres par stratégie, type, Sharpe minimum
- Top performances (Sharpe, Return)
- Export CSV
- Actions : Analyser, Supprimer

### 3. ⚖️ Compare Runs
- **Sélection de 2 à 5 runs** à comparer
- Tableau comparatif côte à côte
- **Graphiques de comparaison** (equity curves, métriques)
- Comparaison des paramètres
- Score et classement global

### 4. 🔬 Analyze Strategy
- Analyse détaillée d'un run spécifique
- **Walk-Forward analysis** (In-Sample vs Out-Sample)
- **Heatmaps** paramètres vs performance
- Distribution des résultats
- Impact des paramètres
- Scatter plots interactifs

## 📦 Installation

```bash
# Installer Streamlit si pas déjà fait
pip install streamlit plotly

# Le reste des dépendances sont déjà dans requirements.txt
```

## 🎯 Lancement

### Option 1 : Lancer le dashboard
```bash
# Depuis la racine du projet
streamlit run optimization\dashboard\app.py
```

### Option 2 : Script de lancement
```bash
# Utiliser le script dédié
python run_dashboard.py
```

Le dashboard s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📁 Structure

```
dashboard/
├── app.py                          # Page d'accueil
├── pages/
│   ├── 1_🚀_Run_Optimization.py   # Lancer une optimisation
│   ├── 2_📋_View_History.py        # Historique
│   ├── 3_⚖️_Compare_Runs.py        # Comparaison
│   └── 4_🔬_Analyze_Strategy.py    # Analyse détaillée
├── components/
│   ├── optimizer_form.py           # Formulaire d'optimisation
│   ├── results_table.py            # Tableaux de résultats
│   ├── charts.py                   # Graphiques Plotly
│   └── metrics.py                  # Cartes de métriques
└── utils/
    └── session_state.py            # Gestion de l'état
```

## 🎨 Fonctionnalités Visuelles

### 📊 Graphiques Plotly Interactifs
- **Equity Curves** : Évolution du capital
- **Drawdown Charts** : Visualisation des pertes maximales
- **Heatmaps** : Paramètres vs Performance
- **Walk-Forward** : In-Sample vs Out-Sample
- **Distribution** : Histogrammes des métriques
- **Scatter Plots** : Return vs Drawdown
- **Parameter Impact** : Effet de chaque paramètre

### 🌗 Dark Mode
- Interface en mode sombre par défaut
- Optimisé pour le confort visuel
- Graphiques adaptés au thème

### 📱 Responsive
- Layout adaptatif
- Colonnes flexibles
- Optimisé pour grands écrans

## 🔧 Utilisation

### Workflow Typique

1. **Lancer une optimisation** (Page 1)
   - Choisir une stratégie (ex: MaSuperStrategie)
   - Sélectionner un preset (quick, standard, exhaustive)
   - Personnaliser si nécessaire
   - Lancer et suivre la progression

2. **Consulter les résultats** (Page 1 ou 4)
   - Métriques principales : Sharpe, Return, Drawdown
   - Meilleurs paramètres trouvés
   - Copier les paramètres pour utilisation

3. **Comparer plusieurs runs** (Page 3)
   - Sélectionner 2+ optimisations
   - Tableau comparatif
   - Graphiques côte à côte
   - Identifier le meilleur

4. **Analyser en détail** (Page 4)
   - Walk-Forward si applicable
   - Heatmaps de paramètres
   - Distribution des résultats
   - Impact des paramètres

5. **Gérer l'historique** (Page 2)
   - Filtrer par critères
   - Exporter en CSV
   - Supprimer les anciens runs

## 📊 Métriques Disponibles

- **Sharpe Ratio** : Rendement ajusté au risque
- **Return (%)** : Rendement total
- **Max Drawdown (%)** : Perte maximale
- **Win Rate (%)** : Taux de trades gagnants
- **Nombre de Trades** : Volume d'activité
- **Avg Win/Loss** : Gains et pertes moyens
- **Profit Factor** : Ratio gains/pertes

## 🎯 Presets Disponibles

- **quick** : Test rapide (peu de combinaisons)
- **standard** : Configuration équilibrée (recommandé)
- **exhaustive** : Recherche complète (beaucoup de combinaisons)
- **walk_forward_quick** : Walk-Forward rapide
- **walk_forward_robust** : Walk-Forward robuste

## 🔍 Filtres et Tri

### Filtres disponibles
- Par stratégie
- Par type d'optimisation
- Par Sharpe minimum
- Par date

### Tri
- Par toutes les métriques
- Ordre croissant/décroissant

## 💾 Export

- **CSV** : Export de l'historique
- **Copie** : Paramètres optimaux en Python
- **Graphiques** : Screenshots via Plotly

## 🚨 Troubleshooting

### Le dashboard ne démarre pas
```bash
# Vérifier que Streamlit est installé
pip install streamlit

# Vérifier la version
streamlit --version
```

### Erreur "Module not found"
```bash
# Installer toutes les dépendances
pip install -r requirements.txt
```

### Graphiques ne s'affichent pas
```bash
# Installer Plotly
pip install plotly
```

### Pas de résultats dans l'historique
- Lancez d'abord une optimisation via la page "Run Optimization"
- Ou utilisez `python optimization/quick_start.py`

## 🔗 Intégration

Le dashboard s'intègre parfaitement avec :
- **Système d'optimisation** : `optimization/optimizer.py`
- **Stockage des résultats** : `optimization/results_storage.py`
- **Configurations** : `optimization/config.py`
- **Stratégies** : `strategies/`

## 📝 Notes

- Les résultats sont sauvegardés automatiquement dans `results/`
- L'historique est persistant entre les sessions
- Utilise le session state de Streamlit pour la navigation
- Dark mode par défaut (modifiable dans le code)

## 🎉 Prochaines Fonctionnalités

- [ ] Export PDF des rapports
- [ ] Notifications en temps réel
- [ ] Multi-threading pour optimisations parallèles
- [ ] Graphiques 3D
- [ ] Machine Learning pour recommandations
- [ ] Intégration avec brokers en temps réel

## 📞 Support

Pour toute question ou problème, consultez :
- Documentation principale : `README.md`
- Code source : `dashboard/`
- Exemples : `optimization/quick_start.py`

---

**🚀 Bon trading et bonnes optimisations !**