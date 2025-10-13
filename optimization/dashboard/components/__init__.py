"""
Composants du dashboard Streamlit
"""

from .charts import (
    create_equity_curve,
    create_drawdown_chart,
    create_comparison_chart,
    create_heatmap,
    create_walk_forward_analysis,
    create_distribution_chart,
    create_scatter_plot,
    create_parameter_impact_chart,
)

from .metrics import (
    display_metric_cards,
    display_detailed_metrics,
    display_parameters_card,
    display_copy_button,
    display_performance_badge,
    display_walk_forward_metrics,
)

from .results_table import (
    display_runs_table,
    display_comparison_table,
    display_parameters_comparison,
    display_detailed_results_table,
    create_filterable_table,
)

from .optimizer_form import (
    get_available_strategies,
    display_strategy_selector,
    display_preset_selector,
    display_optimization_type_selector,
    display_config_customization,
    display_optimization_summary,
    create_optimization_form,
)

__all__ = [
    # Charts
    "create_equity_curve",
    "create_drawdown_chart",
    "create_comparison_chart",
    "create_heatmap",
    "create_walk_forward_analysis",
    "create_distribution_chart",
    "create_scatter_plot",
    "create_parameter_impact_chart",
    # Metrics
    "display_metric_cards",
    "display_detailed_metrics",
    "display_parameters_card",
    "display_copy_button",
    "display_performance_badge",
    "display_walk_forward_metrics",
    # Tables
    "display_runs_table",
    "display_comparison_table",
    "display_parameters_comparison",
    "display_detailed_results_table",
    "create_filterable_table",
    # Forms
    "get_available_strategies",
    "display_strategy_selector",
    "display_preset_selector",
    "display_optimization_type_selector",
    "display_config_customization",
    "display_optimization_summary",
    "create_optimization_form",
]
