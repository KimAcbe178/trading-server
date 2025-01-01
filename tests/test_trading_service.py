import pytest
from decimal import Decimal
from models.trading import OrderRequest
from services.trading_service import TradingService
from utils.exceptions import ValidationError, PositionError

@pytest.mark.asyncio
class TestTradingService:
    async def test_initialization(self, trading_service: TradingService):
        """초기화 테스트"""
        assert trading_service.binance is not None
        assert trading_service.settings is not None

    async def test_place_valid_order(self, trading_service: TradingService):
        """유효한 주문 테스트"""
        order_request = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            quantity=Decimal("0.001"),
            leverage=10
        )
        
        order = await trading_service.place_order(order_request)
        assert order.symbol == "BTCUSDT"
        assert order.side == "BUY"

    async def test_place_invalid_order(self, trading_service: TradingService):
        """잘못된 주문 테스트"""
        order_request = OrderRequest(
            symbol="INVALID",
            side="BUY",
            quantity=Decimal("0.001"),
            leverage=10
        )
        
        with pytest.raises(ValidationError):
            await trading_service.place_order(order_request)

    async def test_position_management(self, trading_service: TradingService):
        """포지션 관리 테스트"""
        # 포지션 생성
        order_request = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            quantity=Decimal("0.001"),
            leverage=10
        )
        await trading_service.place_order(order_request)
        
        # 포지션 조회
        position = await trading_service.get_position("BTCUSDT")
        assert position is not None
        assert position.symbol == "BTCUSDT"
        
        # 포지션 청산
        close_order = await trading_service.close_position("BTCUSDT")
        assert close_order is not None
        
        # 포지션 제거 확인
        position = await trading_service.get_position("BTCUSDT")
        assert position is None