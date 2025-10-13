python scripts/run_optuna_from_yaml.py config/optuna_SqueezeMomentumStrategy.yaml  


python scripts/run_optuna_from_yaml.py config/optuna_MaRSI.yaml  

python scripts/run_optuna_from_yaml.py config/optuna_RSI.yaml  

optuna_SqueezeMomentumStrategy
optuna_MaRSI

  # Filtre de tendance EMA
  ema_trend_period:
    type: "int"
    low: 100
    high: 300
    step: 20
  # Filtre de volume
  volume_sma_period:
    type: "int"
    low: 10
    high: 50
    step: 5
  #
  use_trend_filter : [True, False]
  #
  use_volume_filter : [True, False]
  #
  min_volume_ratio:
    type: "float"
    low: 1.0
    high: 2.0
    step: 0.2
  # Stop loss (pourcentage)
  stop_loss_atr_mult:
     type: "float"
     low: 1.0
     high: 3.0
     step: 0.2
  #
  use_take_profit : [True, False]
  take_profit_pct:
    type: "float"
    low: 0.02
    high: 0.1
    step: 0.01
  # Trailing stop (pourcentage)
  trailing_stop_pct:
    type: "float"
    low: 0.02
    high: 0.1
    step: 0.005
  
  # Activation du trailing stop (pourcentage de profit)
  trailing_activation_pct:
    type: "float"
    low: 0.01
    high: 0.1
    step: 0.005
  #