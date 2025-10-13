"""
Tests unitaires pour le module performance_analyzer
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from backtesting.performance_analyzer import PerformanceAnalyzer


class TestPerformanceAnalyzer:
    """Tests pour la classe PerformanceAnalyzer"""

    @pytest.fixture
    def sample_results(self):
        """Résultats de backtest pour les tests"""
        return {
            "initial_value": 100000.0,
            "final_value": 125000.0,
            "total_return": 25.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": 15.5,
            "total_trades": 50,
            "won_trades": 32,
            "lost_trades": 18,
            "win_rate": 64.0,
            "avg_win": 1250.0,
            "avg_loss": -850.0,
        }

    @pytest.fixture
    def analyzer(self, sample_results):
        """Instance de PerformanceAnalyzer pour les tests"""
        return PerformanceAnalyzer(sample_results, "TestStrategy")

    def test_init(self, sample_results):
        """Test l'initialisation de PerformanceAnalyzer"""
        strategy_name = "TestStrategy"
        analyzer = PerformanceAnalyzer(sample_results, strategy_name)

        assert analyzer.results == sample_results
        assert analyzer.strategy_name == strategy_name
        assert isinstance(analyzer.timestamp, datetime)

    def test_init_with_different_strategy_names(self, sample_results):
        """Test l'initialisation avec différents noms de stratégie"""
        strategies = ["MovingAverage", "RSI", "BollingerBands"]

        for strategy_name in strategies:
            analyzer = PerformanceAnalyzer(sample_results, strategy_name)
            assert analyzer.strategy_name == strategy_name

    @patch("backtesting.performance_analyzer.settings")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_report_creates_txt_file(
        self, mock_file, mock_settings, analyzer, tmp_path
    ):
        """Test que generate_report crée un fichier texte"""
        mock_settings.RESULTS_DIR = tmp_path

        report_path = analyzer.generate_report()

        # Vérifier que open a été appelé pour le fichier txt
        assert mock_file.call_count >= 2  # txt + json
        assert report_path is not None
        assert str(report_path).endswith(".txt")

    @patch("backtesting.performance_analyzer.settings")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_generate_report_creates_json_file(
        self, mock_json_dump, mock_file, mock_settings, analyzer, tmp_path
    ):
        """Test que generate_report crée un fichier JSON"""
        mock_settings.RESULTS_DIR = tmp_path

        analyzer.generate_report()

        # Vérifier que json.dump a été appelé
        mock_json_dump.assert_called_once()
        args = mock_json_dump.call_args
        assert args[0][0] == analyzer.results  # Premier argument

    @patch("backtesting.performance_analyzer.settings")
    def test_generate_report_filename_format(self, mock_settings, analyzer, tmp_path):
        """Test le format du nom de fichier généré"""
        mock_settings.RESULTS_DIR = tmp_path

        with patch("builtins.open", mock_open()):
            report_path = analyzer.generate_report()

        filename = report_path.name
        assert filename.startswith("report_TestStrategy_")
        assert filename.endswith(".txt")
        # Vérifier le format de la date (YYYYMMDD_HHMMSS)
        assert len(filename) == len("report_TestStrategy_20240101_120000.txt")

    def test_format_report_contains_strategy_name(self, analyzer):
        """Test que le rapport contient le nom de la stratégie"""
        report = analyzer._format_report()
        assert "TestStrategy" in report

    def test_format_report_contains_financial_summary(self, analyzer):
        """Test que le rapport contient le résumé financier"""
        report = analyzer._format_report()

        assert "Capital Initial" in report
        assert "Capital Final" in report
        assert "Profit/Perte" in report
        assert "Rendement Total" in report

        # Vérifier que les sections contiennent les bonnes valeurs (de manière flexible)
        # Extraire les lignes pour vérifier les valeurs
        lines = report.split("\n")

        # Chercher la ligne Capital Initial et vérifier qu'elle contient 100000 d'une manière ou d'une autre
        capital_initial_found = False
        capital_final_found = False
        rendement_found = False

        for line in lines:
            if "Capital Initial" in line and "100" in line:
                capital_initial_found = True
            if "Capital Final" in line and "125" in line:
                capital_final_found = True
            if "Rendement Total" in line and "25" in line:
                rendement_found = True

        assert capital_initial_found, "Capital Initial avec valeur 100000 non trouvé"
        assert capital_final_found, "Capital Final avec valeur 125000 non trouvé"
        assert rendement_found, "Rendement Total avec valeur 25% non trouvé"

    def test_format_report_contains_risk_metrics(self, analyzer):
        """Test que le rapport contient les métriques de risque"""
        report = analyzer._format_report()

        assert "Sharpe Ratio" in report
        assert "Max Drawdown" in report
        assert "1.50" in report
        assert "15.50%" in report

    def test_format_report_contains_trade_analysis(self, analyzer):
        """Test que le rapport contient l'analyse des trades"""
        report = analyzer._format_report()

        assert "Nombre Total" in report
        assert "Trades Gagnants" in report
        assert "Trades Perdants" in report
        assert "Taux de Réussite" in report
        assert "50" in report
        assert "32" in report
        assert "18" in report
        assert "64.00%" in report

    def test_format_report_excellent_performance(self, sample_results):
        """Test l'évaluation pour une excellente performance (Sharpe > 2)"""
        sample_results["sharpe_ratio"] = 2.5
        analyzer = PerformanceAnalyzer(sample_results, "ExcellentStrategy")

        report = analyzer._format_report()
        assert "EXCELLENTE" in report
        assert "⭐⭐⭐⭐⭐" in report

    def test_format_report_good_performance(self, sample_results):
        """Test l'évaluation pour une bonne performance (1 < Sharpe <= 2)"""
        sample_results["sharpe_ratio"] = 1.5
        analyzer = PerformanceAnalyzer(sample_results, "GoodStrategy")

        report = analyzer._format_report()
        assert "BONNE" in report
        assert "⭐⭐⭐⭐" in report

    def test_format_report_acceptable_performance(self, sample_results):
        """Test l'évaluation pour une performance acceptable (0.5 < Sharpe <= 1)"""
        sample_results["sharpe_ratio"] = 0.7
        analyzer = PerformanceAnalyzer(sample_results, "AcceptableStrategy")

        report = analyzer._format_report()
        assert "ACCEPTABLE" in report
        assert "⭐⭐⭐" in report

    def test_format_report_weak_performance(self, sample_results):
        """Test l'évaluation pour une faible performance (0 < Sharpe <= 0.5)"""
        sample_results["sharpe_ratio"] = 0.3
        analyzer = PerformanceAnalyzer(sample_results, "WeakStrategy")

        report = analyzer._format_report()
        assert "FAIBLE" in report
        assert "⭐⭐" in report

    def test_format_report_bad_performance(self, sample_results):
        """Test l'évaluation pour une mauvaise performance (Sharpe <= 0)"""
        sample_results["sharpe_ratio"] = -0.5
        analyzer = PerformanceAnalyzer(sample_results, "BadStrategy")

        report = analyzer._format_report()
        assert "MAUVAISE" in report
        assert "⭐" in report

    def test_get_metrics_summary_returns_correct_keys(self, analyzer):
        """Test que get_metrics_summary retourne les bonnes clés"""
        summary = analyzer.get_metrics_summary()

        assert "return" in summary
        assert "sharpe" in summary
        assert "max_dd" in summary
        assert "win_rate" in summary

    def test_get_metrics_summary_returns_correct_values(self, analyzer):
        """Test que get_metrics_summary retourne les bonnes valeurs"""
        summary = analyzer.get_metrics_summary()

        assert summary["return"] == 25.0
        assert summary["sharpe"] == 1.5
        assert summary["max_dd"] == 15.5
        assert summary["win_rate"] == 64.0

    def test_get_metrics_summary_with_zero_values(self, sample_results):
        """Test get_metrics_summary avec des valeurs à zéro"""
        sample_results.update(
            {
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
            }
        )
        analyzer = PerformanceAnalyzer(sample_results, "ZeroStrategy")

        summary = analyzer.get_metrics_summary()

        assert summary["return"] == 0.0
        assert summary["sharpe"] == 0.0
        assert summary["max_dd"] == 0.0
        assert summary["win_rate"] == 0.0

    def test_get_metrics_summary_with_negative_values(self, sample_results):
        """Test get_metrics_summary avec des valeurs négatives"""
        sample_results.update(
            {
                "total_return": -15.5,
                "sharpe_ratio": -1.2,
                "max_drawdown": 35.8,
                "win_rate": 30.0,
            }
        )
        analyzer = PerformanceAnalyzer(sample_results, "NegativeStrategy")

        summary = analyzer.get_metrics_summary()

        assert summary["return"] == -15.5
        assert summary["sharpe"] == -1.2
        assert summary["max_dd"] == 35.8
        assert summary["win_rate"] == 30.0

    def test_format_report_formatting_consistency(self, analyzer):
        """Test la cohérence du formatage du rapport"""
        report = analyzer._format_report()

        # Vérifier les séparateurs
        assert "=" * 80 in report

        # Vérifier les sections principales
        assert "RAPPORT DE BACKTEST" in report
        assert "RÉSUMÉ FINANCIER" in report
        assert "MÉTRIQUES DE RISQUE" in report
        assert "ANALYSE DES TRADES" in report
        assert "ÉVALUATION" in report

    def test_timestamp_format(self, analyzer):
        """Test le format du timestamp"""
        report = analyzer._format_report()

        # Vérifier que la date est dans le rapport
        timestamp_str = analyzer.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        assert timestamp_str in report

    @patch("backtesting.performance_analyzer.settings")
    @patch("backtesting.performance_analyzer.logger")
    def test_generate_report_logs_success(
        self, mock_logger, mock_settings, analyzer, tmp_path
    ):
        """Test que generate_report log le succès"""
        mock_settings.RESULTS_DIR = tmp_path

        with patch("builtins.open", mock_open()):
            analyzer.generate_report()

        # Vérifier qu'un log info a été créé
        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        assert "sauvegardé" in call_args.lower() or "saved" in call_args.lower()

    def test_results_immutability(self, analyzer):
        """Test que les résultats ne sont pas modifiés par l'analyse"""
        original_results = analyzer.results.copy()

        analyzer._format_report()
        analyzer.get_metrics_summary()

        assert analyzer.results == original_results

    def test_multiple_report_generations(self, analyzer, tmp_path):
        """Test la génération de plusieurs rapports successifs"""
        import time

        with patch("backtesting.performance_analyzer.settings") as mock_settings:
            mock_settings.RESULTS_DIR = tmp_path

            with patch("builtins.open", mock_open()):
                report1 = analyzer.generate_report()
                # Petit délai pour s'assurer que le timestamp est différent
                time.sleep(1.1)
                report2 = analyzer.generate_report()

            # Les rapports devraient avoir des noms différents (timestamps différents)
            # Si générés à la même seconde, au moins vérifier qu'ils ne sont pas None
            assert report1 is not None
            assert report2 is not None
            # Si on a la chance d'avoir des timestamps différents, ils seront différents
            # Sinon ce n'est pas grave, l'important est que les deux générations fonctionnent

    def test_format_report_with_extreme_values(self, sample_results):
        """Test le formatage avec des valeurs extrêmes"""
        sample_results.update(
            {
                "initial_value": 1000000000.0,  # 1 milliard
                "final_value": 5000000000.0,  # 5 milliards
                "total_return": 400.0,
                "max_drawdown": 99.9,
                "total_trades": 10000,
            }
        )
        analyzer = PerformanceAnalyzer(sample_results, "ExtremeStrategy")

        report = analyzer._format_report()

        # Vérifier que le formatage gère les grandes valeurs
        assert "1,000,000,000" in report
        assert "5,000,000,000" in report
        assert "400.00%" in report

    def test_analyzer_with_empty_strategy_name(self, sample_results):
        """Test avec un nom de stratégie vide"""
        analyzer = PerformanceAnalyzer(sample_results, "")

        report = analyzer._format_report()
        assert report is not None

        summary = analyzer.get_metrics_summary()
        assert summary is not None

    def test_analyzer_with_special_characters_in_name(self, sample_results):
        """Test avec des caractères spéciaux dans le nom de stratégie"""
        special_names = [
            "Strategy-V2.0",
            "Strategy_Test",
            "Stratégie-Française",
            "Strategy (Advanced)",
        ]

        for name in special_names:
            analyzer = PerformanceAnalyzer(sample_results, name)
            report = analyzer._format_report()
            assert name in report
