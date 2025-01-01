import pytest
import asyncio
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from services.binance_service import BinanceService
from services.settings_service import SettingsService
from services.trading_service import TradingService
from config.env import EnvConfig

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """비동기 테스트를 위한 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_settings() -> dict:
    """테스트용 설정"""
    return {
        "trading": {
            "default_leverage": 10,
            "default_quantity": 0.01,
            "risk_limit": 0.1,
            "max_positions": 5,
            "allowed_symbols": ["BTCUSDT", "ETHUSDT"]
        },
        "api": {
            "testnet": True,
            "recv_window": 5000,
            "position_mode": False
        }
    }

@pytest.fixture
async def binance_service() -> BinanceService:
    """바이낸스 서비스 픽스처"""
    service = BinanceService()
    await service.initialize()
    yield service
    await service.cleanup()

@pytest.fixture
def settings_service(tmp_path: Path, test_settings: dict) -> SettingsService:
    """설정 서비스 픽스처"""
    # 임시 설정 파일 생성
    settings_file = tmp_path / "settings.json"
    settings_service = SettingsService()
    settings_service.settings_file = settings_file
    settings_service._save_settings()
    return settings_service

@pytest.fixture
async def trading_service(
    binance_service: BinanceService,
    settings_service: SettingsService
) -> TradingService:
    """거래 서비스 픽스처"""
    service = TradingService(binance_service, settings_service)
    await service.initialize()
    return service

@pytest.fixture
def test_client(trading_service: TradingService) -> TestClient:
    """FastAPI 테스트 클라이언트"""
    from main import app
    return TestClient(app)