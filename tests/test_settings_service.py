import pytest
from services.settings_service import SettingsService
from utils.exceptions import ValidationError

class TestSettingsService:
    def test_load_settings(self, settings_service: SettingsService):
        """설정 로드 테스트"""
        settings = settings_service.get_settings()
        assert settings is not None
        assert settings.trading is not None
        assert settings.api is not None

    def test_update_trading_settings(self, settings_service: SettingsService):
        """거래 설정 업데이트 테스트"""
        new_settings = {
            "default_leverage": 20,
            "default_quantity": 0.02,
            "risk_limit": 0.2,
            "max_positions": 3,
            "allowed_symbols": ["BTCUSDT"]
        }
        
        settings_service.update_trading_settings(new_settings)
        trading_settings = settings_service.get_trading_settings()
        
        assert trading_settings.default_leverage == 20
        assert trading_settings.default_quantity == 0.02
        assert trading_settings.risk_limit == 0.2

    def test_validate_symbol(self, settings_service: SettingsService):
        """심볼 유효성 검사 테스트"""
        assert settings_service.validate_symbol("BTCUSDT")
        assert not settings_service.validate_symbol("INVALID")

    def test_validate_leverage(self, settings_service: SettingsService):
        """레버리지 유효성 검사 테스트"""
        assert settings_service.validate_leverage(10)
        assert not settings_service.validate_leverage(0)
        assert not settings_service.validate_leverage(126)