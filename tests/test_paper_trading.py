"""
Tests pour le module Paper Trading
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
# Importer les modules à tester
from paper_trading.portfolio_state import PortfolioStateManager
from paper_trading.circuit_breaker import CircuitBreaker
from paper_trading.alpaca_store import AlpacaStore
from paper_trading.multi_strategy_runner import StrategyInstance


class TestPortfolioStateManager:
    """Tests pour le gestionnaire d'état du portefeuille"""
    
    def test_init(self, tmp_path):
        """Test l'initialisation du manager"""
        config = {
            'portfolio_state': {
                'enabled': True,
                'backup_dir': tmp_path / 'test_backups',
                'save_interval_seconds': 60,
                'max_backups': 10,
                'compression': False,
                'save_on_trade': True,
                'save_on_shutdown': True,
            }
        }
        
        manager = PortfolioStateManager(config)
        assert manager.backup_dir.exists()
        assert manager.config['enabled'] == True
    
    def test_save_and_load_state(self, tmp_path):
        """Test la sauvegarde et le chargement d'état"""
        config = {
            'portfolio_state': {
                'enabled': True,
                'backup_dir': tmp_path / 'test_backups',
                'compression': False,
                'rotate_backups': False,
            }
        }
        
        manager = PortfolioStateManager(config)
        
        # Mettre à jour l'état
        test_data = {
            'portfolio_value': 100000,
            'cash': 50000,
            'positions': {'AAPL': 100}
        }
        manager.update_state('account', test_data)
        
        # Sauvegarder
        manager.save_state()
        
        # Charger
        loaded_state = manager.load_latest_state()
        assert loaded_state is not None
        assert loaded_state['account'] == test_data
    
    def test_state_compression(self, tmp_path):
        """Test la compression des états"""
        config = {
            'portfolio_state': {
                'enabled': True,
                'backup_dir': tmp_path / 'test_backups',
                'compression': True,
                'rotate_backups': False,
            }
        }
        
        manager = PortfolioStateManager(config)
        manager.update_state('test', {'data': 'test' * 1000})
        manager.save_state()
        
        # Vérifier qu'un fichier compressé existe
        gz_files = list(manager.backup_dir.glob('*.gz'))
        assert len(gz_files) > 0


class TestCircuitBreaker:
    """Tests pour le circuit breaker"""
    
    def test_init(self):
        """Test l'initialisation du circuit breaker"""
        config = {
            'circuit_breakers': {
                'enabled': True,
                'max_drawdown_pct': 0.20,
                'max_daily_trades': 50,
                'max_consecutive_losses': 5,
                'max_daily_loss_pct': 0.05,
                'pause_duration_minutes': 60,
                'market_hours_only': True,
            }
        }
        
        breaker = CircuitBreaker(config)
        assert breaker.config['enabled'] == True
        assert breaker.paused == False
    
    def test_drawdown_trigger(self):
        """Test le déclenchement du drawdown"""
        config = {
            'circuit_breakers': {
                'enabled': True,
                'max_drawdown_pct': 0.10,  # 10%
                'pause_duration_minutes': 60,
            }
        }
        
        breaker = CircuitBreaker(config)
        breaker.initial_capital = 100000
        breaker.peak_value = 100000
        
        # Simuler une perte de 15%
        can_trade = breaker.check_conditions(85000)
        assert can_trade == False
        assert breaker.paused == True
    
    def test_consecutive_losses(self):
        """Test les pertes consécutives"""
        config = {
            'circuit_breakers': {
                'enabled': True,
                'max_consecutive_losses': 3,
                'pause_duration_minutes': 60,
            }
        }
        
        breaker = CircuitBreaker(config)
        
        # Enregistrer 3 pertes consécutives
        breaker.record_trade('AAPL', 'sell', 100, 150, pnl=-100)
        breaker.record_trade('MSFT', 'sell', 50, 200, pnl=-50)
        breaker.record_trade('GOOGL', 'sell', 25, 1000, pnl=-200)
        
        assert breaker.consecutive_losses == 3
        assert breaker.breakers_status['consecutive_losses']['triggered'] == True
    
    def test_daily_trade_limit(self):
        """Test la limite de trades quotidiens"""
        config = {
            'circuit_breakers': {
                'enabled': True,
                'max_daily_trades': 5,
                'pause_duration_minutes': 60,
            }
        }
        
        breaker = CircuitBreaker(config)
        today = datetime.now().date()
        
        # Enregistrer 6 trades
        for i in range(6):
            breaker.record_trade(f'STOCK{i}', 'buy', 100, 100)
        
        assert len(breaker.daily_trades[today]) == 6
        assert breaker.breakers_status['daily_trades']['triggered'] == True


class TestAlpacaStore:
    """Tests pour l'Alpaca Store"""
    
    @patch('paper_trading.alpaca_store.tradeapi.REST')
    def test_init(self, mock_rest):
        """Test l'initialisation du store"""
        # Mock de l'API
        mock_api = MagicMock()
        mock_account = MagicMock()
        mock_account.cash = '100000'
        mock_account.buying_power = '100000'
        mock_api.get_account.return_value = mock_account
        mock_rest.return_value = mock_api
        
        store = AlpacaStore(
            api_key='test_key',
            secret_key='test_secret',
            base_url='https://paper-api.alpaca.markets'
        )
        
        assert store.api is not None
        mock_api.get_account.assert_called_once()
    
    @patch('paper_trading.alpaca_store.tradeapi.REST')
    def test_submit_order(self, mock_rest):
        """Test la soumission d'ordre"""
        # Mock de l'API
        mock_api = MagicMock()
        mock_order = MagicMock()
        mock_order.id = 'order123'
        mock_api.submit_order.return_value = mock_order
        mock_rest.return_value = mock_api
        
        # Créer un mock account
        mock_account = MagicMock()
        mock_account.cash = '100000'
        mock_account.buying_power = '100000'
        mock_api.get_account.return_value = mock_account
        
        store = AlpacaStore(
            api_key='test_key',
            secret_key='test_secret'
        )
        
        order = store.submit_order(
            symbol='AAPL',
            qty=100,
            side='buy',
            order_type='market'
        )
        
        assert order.id == 'order123'
        mock_api.submit_order.assert_called_once()


class TestMultiStrategyRunner:
    """Tests pour le runner multi-stratégies"""
    
    def test_strategy_instance_init(self):
        """Test l'initialisation d'une instance de stratégie"""
        config = {
            'name': 'TestStrategy',
            'symbols': ['AAPL', 'MSFT'],
            'capital_allocation': 50000,
            'params': {'period': 20}
        }
        
        mock_store = MagicMock()
        instance = StrategyInstance(
            name='TestStrategy',
            config=config,
            store=mock_store
        )
        
        assert instance.name == 'TestStrategy'
        assert instance.config == config
        assert instance.running == False


@pytest.fixture
def temp_config(tmp_path):
    """Fixture pour créer une configuration temporaire"""
    return {
        'portfolio_state': {
            'enabled': True,
            'backup_dir': tmp_path / 'backups',
            'save_interval_seconds': 60,
            'max_backups': 10,
            'compression': False,
        },
        'circuit_breakers': {
            'enabled': True,
            'max_drawdown_pct': 0.20,
            'max_daily_trades': 50,
            'max_consecutive_losses': 5,
            'pause_duration_minutes': 60,
        }
    }


def test_imports():
    """Test que tous les imports fonctionnent"""
    from paper_trading import PaperTradingEngine
    from paper_trading import AlpacaStore
    from paper_trading import AlpacaBroker
    from paper_trading import AlpacaData
    from paper_trading import PortfolioStateManager
    from paper_trading import CircuitBreaker
    from paper_trading import MultiStrategyRunner
    
    assert PaperTradingEngine is not None
    assert AlpacaStore is not None


def test_config_exists():
    """Test que la configuration existe"""
    from config.paper_trading_config import PAPER_TRADING_CONFIG
    
    assert 'alpaca' in PAPER_TRADING_CONFIG
    assert 'strategies' in PAPER_TRADING_CONFIG
    assert 'circuit_breakers' in PAPER_TRADING_CONFIG
    assert 'portfolio_state' in PAPER_TRADING_CONFIG


def test_env_file_example():
    """Test que le fichier .env.example existe"""
    env_example = Path('.env.example')
    assert env_example.exists(), "Le fichier .env.example doit exister"
    
    # Vérifier le contenu
    content = env_example.read_text()
    assert 'ALPACA_API_KEY' in content
    assert 'ALPACA_SECRET_KEY' in content


# Tests d'intégration (nécessitent les clés API)
@pytest.mark.integration
class TestIntegration:
    """Tests d'intégration avec Alpaca (nécessitent les clés API)"""
    
    @pytest.mark.skipif(not os.getenv('ALPACA_API_KEY'), reason="Clés API non disponibles")
    def test_alpaca_connection(self):
        """Test la connexion réelle à Alpaca"""
        from paper_trading.alpaca_store import AlpacaStore
        
        store = AlpacaStore(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url='https://paper-api.alpaca.markets'
        )
        
        account = store.get_account()
        assert account is not None
        assert float(account.cash) >= 0
    
    @pytest.mark.skipif(not os.getenv('TELEGRAM_BOT_TOKEN'), reason="Token Telegram non disponible")
    def test_telegram_connection(self):
        """Test la connexion Telegram"""
        from monitoring.telegram_notifier import TelegramNotifier
        
        notifier = TelegramNotifier(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            chat_id=os.getenv('TELEGRAM_CHAT_ID')
        )
        
        result = notifier.test_connection()
        assert result == True