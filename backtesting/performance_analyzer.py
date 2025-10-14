"""
Analyse des performances et génération de rapports
"""

import json
from datetime import datetime
from pathlib import Path

from config import settings
from monitoring.logger import setup_logger

logger = setup_logger("performance")


class PerformanceAnalyzer:
    """Analyse les performances d'un backtest"""

    def __init__(self, results, strategy_name):
        self.results = results
        self.strategy_name = strategy_name
        self.timestamp = datetime.now()

    def generate_report(self):
        """Génère un rapport complet"""
        report_filename = (
            f"report_{self.strategy_name}_"
            f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        report_path = settings.RESULTS_DIR / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(self._format_report())

        # Sauvegarder aussi en JSON
        json_path = report_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Rapport sauvegardé: {report_path}")
        return report_path

    def _format_report(self):
        """Formate le rapport en texte"""
        r = self.results

        report = f"""
{'='*80}
RAPPORT DE BACKTEST - {self.strategy_name}
{'='*80}
Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

RÉSUMÉ FINANCIER
{'='*80}
Capital Initial:        ${r['initial_value']:>15,.2f}
Capital Final:          ${r['final_value']:>15,.2f}
Profit/Perte:           ${r['final_value'] - r['initial_value']:>15,.2f}
Rendement Total:        {r['total_return']:>15.2f}%
Rendement Annuel:       {r['annual_return']:>15.2f}%

MÉTRIQUES DE RISQUE
{'='*80}
Sharpe Ratio:           {r['sharpe_ratio']:>15.2f}
Max Drawdown:           {r['max_drawdown']:>15.2f}%
Calmar Ratio:           {r['calmar_ratio']:>15.2f}
VWR:                    {r['vwr']:>15.2f}

ANALYSE DES TRADES
{'='*80}
Nombre Total:           {r['total_trades']:>15}
Trades Gagnants:        {r['won_trades']:>15}
Trades Perdants:        {r['lost_trades']:>15}
Taux de Réussite:       {r['win_rate']:>15.2f}%
Gain Moyen:             ${r['avg_win']:>15.2f}
Perte Moyenne:          ${r['avg_loss']:>15.2f}

ÉVALUATION
{'='*80}
"""

        # Évaluation de la performance
        if r["sharpe_ratio"] > 2:
            report += "Performance: EXCELLENTE ⭐⭐⭐⭐⭐\n"
        elif r["sharpe_ratio"] > 1:
            report += "Performance: BONNE ⭐⭐⭐⭐\n"
        elif r["sharpe_ratio"] > 0.5:
            report += "Performance: ACCEPTABLE ⭐⭐⭐\n"
        elif r["sharpe_ratio"] > 0:
            report += "Performance: FAIBLE ⭐⭐\n"
        else:
            report += "Performance: MAUVAISE ⭐\n"

        report += f"\n{'='*80}\n"

        return report

    def get_metrics_summary(self):
        """Retourne un résumé des métriques principales"""
        return {
            "return": self.results["total_return"],
            "annual_return": self.results["annual_return"],
            "sharpe": self.results["sharpe_ratio"],
            "max_drawdown": self.results["max_drawdown"],
            "calmar_ratio": self.results["calmar_ratio"],
            "vwr": self.results["vwr"],
            "max_dd": self.results["max_drawdown"],
            "win_rate": self.results["win_rate"],
        }
