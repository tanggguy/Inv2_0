"""
Multi-Symbol Exporter

Module d'export des résultats de backtest multi-symbole dans 3 formats:
- JSON: Pour automatisation et parsing
- CSV: Pour analyse quantitative (Excel, Python, R)
- HTML: Pour rapports visuels avec graphiques interactifs
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from monitoring.logger import setup_logger

logger = setup_logger("multi_symbol_exporter")


class MultiSymbolExporter:
    """
    Exporteur de résultats multi-symbole

    Formats supportés:
    - JSON (summary.json)
    - CSV (symbol_metrics.csv, trade_log.csv, etc.)
    - HTML (report.html avec graphiques Plotly)
    """

    def __init__(self, results: Dict, output_dir: str = None):
        """
        Initialise l'exporteur

        Args:
            results: Dict complet des résultats
                    {aggregated: {...}, by_symbol: {...}, portfolio_info: {...}}
            output_dir: Répertoire de sortie
                       Si None, crée: results/multi_symbol/{strategy}_{timestamp}/
        """
        self.results = results
        self.aggregated = results.get("aggregated", {})
        self.by_symbol = results.get("by_symbol", {})
        self.portfolio_info = results.get("portfolio_info", {})

        # Créer le répertoire de sortie
        if output_dir is None:
            strategy = self.aggregated.get("strategy", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"results/multi_symbol/{strategy}_{timestamp}"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporteur initialisé: {self.output_dir}")

    def export_all(self) -> Dict[str, str]:
        """
        Export dans tous les formats + graphiques individuels

        Returns:
            Dict avec les chemins des fichiers créés
        """
        logger.info("📦 Export de tous les formats...")

        files = {}

        # JSON
        files["json"] = self.export_json()

        # CSV Suite
        csv_files = self.export_csv_suite()
        files.update(csv_files)

        # HTML avec graphiques intégrés
        files["html"] = self.export_html()

        # Graphiques individuels
        chart_files = self.export_individual_charts()
        files.update(chart_files)

        logger.info(f"✓ Export terminé: {len(files)} fichiers créés")
        logger.info(f"📁 Dossier: {self.output_dir}")

        return files

    def export_json(self, filename: str = "summary.json") -> str:
        """
        Export en JSON

        Args:
            filename: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / filename

        # Préparer les données
        data = {
            "metadata": {
                "strategy": self.aggregated.get("strategy", "N/A"),
                "symbols": self.aggregated.get("symbols", []),
                "period": self.aggregated.get("period", {}),
                "timestamp": self.aggregated.get("timestamp", ""),
                "total_capital": self.portfolio_info.get("total_capital", 0),
                "max_positions": self.portfolio_info.get("max_positions"),
            },
            "portfolio": {
                "initial_value": self.aggregated.get("initial_value", 0),
                "final_value": self.aggregated.get("final_value", 0),
                "absolute_pnl": self.aggregated.get("absolute_pnl", 0),
                "portfolio_return": self.aggregated.get("portfolio_return", 0),
                "portfolio_sharpe": self.aggregated.get("portfolio_sharpe", 0),
                "portfolio_max_drawdown": self.aggregated.get(
                    "portfolio_max_drawdown", 0
                ),
                "total_trades": self.aggregated.get("total_trades", 0),
                "portfolio_win_rate": self.aggregated.get("portfolio_win_rate", 0),
            },
            "symbols": {},
            "allocations": self.portfolio_info.get("allocations", {}),
            "weights": self.portfolio_info.get("weights", {}),
            "pnl_contributions": self.aggregated.get("pnl_contributions", {}),
        }

        # Ajouter résultats par symbole
        for symbol, results in self.by_symbol.items():
            data["symbols"][symbol] = {
                "allocated_capital": results.get("allocated_capital", 0),
                "weight": results.get("weight", 0),
                "initial_value": results.get("initial_value", 0),
                "final_value": results.get("final_value", 0),
                "absolute_pnl": results.get("absolute_pnl", 0),
                "return_pct": results.get("total_return", 0),
                "sharpe_ratio": results.get("sharpe_ratio", 0),
                "max_drawdown": results.get("max_drawdown", 0),
                "total_trades": results.get("total_trades", 0),
                "won_trades": results.get("won_trades", 0),
                "lost_trades": results.get("lost_trades", 0),
                "win_rate": results.get("win_rate", 0),
            }

        # Écrire JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ JSON exporté: {filepath}")
        return str(filepath)

    def export_csv_suite(self) -> Dict[str, str]:
        """
        Export suite de fichiers CSV

        Returns:
            Dict avec chemins des fichiers CSV créés
        """
        files = {}

        # 1. Métriques par symbole
        files["symbol_metrics"] = self._export_symbol_metrics_csv()

        # 2. Allocation du capital
        files["allocations"] = self._export_allocations_csv()

        # 3. Contributions P&L
        files["contributions"] = self._export_contributions_csv()

        return files

    def _export_symbol_metrics_csv(self) -> str:
        """Export métriques par symbole en CSV"""
        filepath = self.output_dir / "symbol_metrics.csv"

        rows = []
        for symbol, results in self.by_symbol.items():
            # Obtenir contribution P&L
            pnl_contrib = self.aggregated.get("pnl_contributions", {}).get(symbol, {})
            contrib_pct = pnl_contrib.get("percentage", 0) if pnl_contrib else 0

            row = {
                "symbol": symbol,
                "allocated_capital": results.get("allocated_capital", 0),
                "weight": results.get("weight", 0),
                "return_pct": results.get("total_return", 0),
                "sharpe_ratio": results.get("sharpe_ratio", 0),
                "max_drawdown": results.get("max_drawdown", 0),
                "total_trades": results.get("total_trades", 0),
                "won_trades": results.get("won_trades", 0),
                "lost_trades": results.get("lost_trades", 0),
                "win_rate": results.get("win_rate", 0),
                "absolute_pnl": results.get("absolute_pnl", 0),
                "pnl_contribution_pct": contrib_pct,
                "final_value": results.get("final_value", 0),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        # Trier par return décroissant
        df = df.sort_values("return_pct", ascending=False)
        df.to_csv(filepath, index=False, float_format="%.2f")

        logger.info(f"✓ CSV métriques exporté: {filepath}")
        return str(filepath)

    def _export_allocations_csv(self) -> str:
        """Export allocation du capital en CSV"""
        filepath = self.output_dir / "capital_allocation.csv"

        rows = []
        allocations = self.portfolio_info.get("allocations", {})
        weights = self.portfolio_info.get("weights", {})

        for symbol in sorted(allocations.keys()):
            row = {
                "symbol": symbol,
                "allocated_capital": allocations.get(symbol, 0),
                "weight": weights.get(symbol, 0),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, float_format="%.4f")

        logger.info(f"✓ CSV allocation exporté: {filepath}")
        return str(filepath)

    def _export_contributions_csv(self) -> str:
        """Export contributions P&L en CSV"""
        filepath = self.output_dir / "pnl_contributions.csv"

        rows = []
        contributions = self.aggregated.get("pnl_contributions", {})

        for symbol in sorted(contributions.keys()):
            contrib = contributions[symbol]
            row = {
                "symbol": symbol,
                "absolute_pnl": contrib.get("absolute", 0),
                "contribution_pct": contrib.get("percentage", 0),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        # Trier par contribution décroissante
        df = df.sort_values("contribution_pct", ascending=False)
        df.to_csv(filepath, index=False, float_format="%.2f")

        logger.info(f"✓ CSV contributions exporté: {filepath}")
        return str(filepath)

    def export_individual_charts(self) -> Dict[str, str]:
        """
        Exporte chaque graphique Plotly dans un fichier HTML séparé

        Returns:
            Dict {chart_name: filepath}
        """
        try:
            from backtesting.plotly_charts import PlotlyChartsGenerator

            chart_gen = PlotlyChartsGenerator(self.results)
            charts = chart_gen.generate_all_charts()

            exported_files = {}

            for chart_name, fig in charts.items():
                if fig:
                    filename = f"chart_{chart_name}.html"
                    filepath = self.output_dir / filename

                    # Export standalone HTML
                    fig.write_html(
                        str(filepath),
                        include_plotlyjs="cdn",
                        config={"displayModeBar": True, "responsive": True},
                    )

                    exported_files[chart_name] = str(filepath)

            logger.info(f"✓ {len(exported_files)} graphiques exportés individuellement")
            return exported_files

        except Exception as e:
            logger.error(f"Erreur export graphiques: {e}")
            return {}

    def export_html(self, filename: str = "report.html") -> str:
        """
        Export rapport HTML avec graphiques Plotly

        Args:
            filename: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        filepath = self.output_dir / filename

        # Générer graphiques Plotly
        plotly_html = self._generate_plotly_charts()

        # Générer le HTML complet
        html = self._generate_html_report(plotly_html)

        # Écrire le fichier
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"✓ HTML exporté: {filepath}")
        return str(filepath)

    def _generate_plotly_charts(self) -> str:
        """
        Génère tous les graphiques Plotly en HTML

        Returns:
            String HTML avec tous les graphiques
        """
        try:
            from backtesting.plotly_charts import PlotlyChartsGenerator

            # Créer générateur
            chart_gen = PlotlyChartsGenerator(self.results)

            # Générer tous les graphiques
            charts = chart_gen.generate_all_charts()

            # Convertir en HTML
            html_parts = []

            # Premier graphique avec Plotly.js complet
            first_chart = True

            for chart_name, fig in charts.items():
                if fig:
                    # Premier graphique : inclure Plotly.js
                    # Suivants : juste les divs
                    if first_chart:
                        chart_html = fig.to_html(
                            include_plotlyjs="cdn",
                            div_id=f"chart_{chart_name}",
                            config={"displayModeBar": True, "responsive": True},
                        )
                        first_chart = False
                    else:
                        chart_html = fig.to_html(
                            include_plotlyjs=False,
                            div_id=f"chart_{chart_name}",
                            config={"displayModeBar": True, "responsive": True},
                        )

                    # Wrapper avec titre
                    html_parts.append(
                        f"""
                    <div class="chart-container">
                        <h3 class="chart-title">{self._get_chart_title(chart_name)}</h3>
                        {chart_html}
                    </div>
                    """
                    )

            logger.info(f"✓ {len(charts)} graphiques Plotly générés pour HTML")

            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Erreur génération graphiques Plotly: {e}")
            import traceback

            traceback.print_exc()
            return '<p style="color: red;">⚠️ Graphiques non disponibles - Vérifier installation de Plotly</p>'

    def _get_chart_title(self, chart_name: str) -> str:
        """
        Retourne un titre lisible pour chaque graphique

        Args:
            chart_name: Nom du graphique

        Returns:
            Titre formaté
        """
        titles = {
            "equity_curves": "📈 Equity Curves Comparées",
            "cumulative_returns": "📊 Returns Cumulés (Base 100)",
            "correlation_heatmap": "🔗 Matrice de Corrélation",
            "return_vs_drawdown": "📉 Return vs Drawdown",
            "pnl_contributions": "💰 Contributions P&L",
            "rolling_correlations": "🔄 Rolling Correlations",
        }
        return titles.get(chart_name, chart_name.replace("_", " ").title())

    def _generate_html_report(self, plotly_charts_html: str = "") -> str:
        """
        Génère le rapport HTML complet avec graphiques Plotly

        Args:
            plotly_charts_html: HTML des graphiques Plotly

        Returns:
            String HTML
        """
        agg = self.aggregated
        strategy = agg.get("strategy", "N/A")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # En-tête HTML avec Plotly.js
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {strategy} - {timestamp}</title>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card-title {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .card-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .card.positive {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .card.negative {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
        }}
        
        tbody tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        tbody tr:hover {{
            background: #e9ecef;
        }}
        
        .positive-value {{
            color: #38ef7d;
            font-weight: bold;
        }}
        
        .negative-value {{
            color: #ee0979;
            font-weight: bold;
        }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            color: #667eea;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Multi-Symbol Backtest Report</h1>
            <p>Strategy: <strong>{strategy}</strong></p>
            <p>{timestamp}</p>
        </div>
        
        <div class="content">
"""

        # Section: Portfolio Performance
        html += self._generate_portfolio_section()

        # Section: Graphiques Plotly
        if plotly_charts_html:
            html += f"""
            <div class="section">
                <h2>📈 Graphiques Interactifs</h2>
                {plotly_charts_html}
            </div>
"""

        # Section: Symbol Performance
        html += self._generate_symbols_table()

        # Section: P&L Contributions
        html += self._generate_contributions_section()

        # Pied de page
        html += """
        </div>
        
        <div class="footer">
            <p>Generated by Multi-Symbol Backtest Engine with Plotly Charts</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _generate_portfolio_section(self) -> str:
        """Génère la section performance du portfolio"""
        agg = self.aggregated

        # Déterminer classe CSS selon performance
        ret = agg.get("portfolio_return", 0)
        card_class = "positive" if ret > 0 else "negative"

        html = f"""
            <div class="section">
                <h2>📈 Performance Globale du Portfolio</h2>
                
                <div class="cards">
                    <div class="card {card_class}">
                        <div class="card-title">Return Total</div>
                        <div class="card-value">{ret:+.2f}%</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-title">Sharpe Ratio</div>
                        <div class="card-value">{agg.get('portfolio_sharpe', 0):.2f}</div>
                    </div>
                    
                    <div class="card negative">
                        <div class="card-title">Max Drawdown</div>
                        <div class="card-value">{agg.get('portfolio_max_drawdown', 0):.1f}%</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-title">Total Trades</div>
                        <div class="card-value">{agg.get('total_trades', 0)}</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-title">Win Rate</div>
                        <div class="card-value">{agg.get('portfolio_win_rate', 0):.1f}%</div>
                    </div>
                    
                    <div class="card {card_class}">
                        <div class="card-title">P&L Total</div>
                        <div class="card-value">${agg.get('absolute_pnl', 0):,.0f}</div>
                    </div>
                </div>
            </div>
"""
        return html

    def _generate_symbols_table(self) -> str:
        """Génère le tableau des symboles"""
        html = """
            <div class="section">
                <h2>📋 Performance par Symbole</h2>
                
                <table>
                    <thead>
                        <tr>
                            <th>Symbole</th>
                            <th>Capital Alloué</th>
                            <th>Poids</th>
                            <th>Return (%)</th>
                            <th>Sharpe</th>
                            <th>Drawdown (%)</th>
                            <th>Trades</th>
                            <th>Win Rate (%)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        # Trier symboles par return
        sorted_symbols = sorted(
            self.by_symbol.items(),
            key=lambda x: x[1].get("total_return", 0),
            reverse=True,
        )

        for symbol, results in sorted_symbols:
            ret = results.get("total_return", 0)
            ret_class = "positive-value" if ret > 0 else "negative-value"

            html += f"""
                        <tr>
                            <td><strong>{symbol}</strong></td>
                            <td>${results.get('allocated_capital', 0):,.0f}</td>
                            <td>{results.get('weight', 0):.1%}</td>
                            <td class="{ret_class}">{ret:+.2f}%</td>
                            <td>{results.get('sharpe_ratio', 0):.2f}</td>
                            <td>{results.get('max_drawdown', 0):.1f}%</td>
                            <td>{results.get('total_trades', 0)}</td>
                            <td>{results.get('win_rate', 0):.1f}%</td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
"""
        return html

    def _generate_contributions_section(self) -> str:
        """Génère la section contributions P&L"""
        html = """
            <div class="section">
                <h2>💰 Contributions au P&L</h2>
                
                <table>
                    <thead>
                        <tr>
                            <th>Symbole</th>
                            <th>P&L Absolu</th>
                            <th>Contribution (%)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        contributions = self.aggregated.get("pnl_contributions", {})

        # Trier par contribution décroissante
        sorted_contrib = sorted(
            contributions.items(), key=lambda x: x[1].get("percentage", 0), reverse=True
        )

        for symbol, contrib in sorted_contrib:
            pnl = contrib.get("absolute", 0)
            pnl_class = "positive-value" if pnl > 0 else "negative-value"

            html += f"""
                        <tr>
                            <td><strong>{symbol}</strong></td>
                            <td class="{pnl_class}">${pnl:,.2f}</td>
                            <td>{contrib.get('percentage', 0):.1f}%</td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
"""
        return html
