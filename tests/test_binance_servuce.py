import pytest
from decimal import Decimal
from models.trading import OrderRequest
from services.binance_service import BinanceService
from utils.exceptions import BinanceError

@pytest.mark.asyncio
class TestBinanceService:
    async def test_initialization(self, binance_service: BinanceService):
        """초기화 테스트"""
        assert binance_service._initialized
        assert binance_service.client is not None

    async def test_get_mark_price(self, binance_service: BinanceService):
        """마크 가격 조회 테스트"""
        price = await binance_service.get_mark_price("BTCUSDT")
        assert isinstance(price, Decimal)
        assert price > 0

    async def test_get_position(self, binance_service: BinanceService):
        """포지션 조회 테스트"""
        position = await binance_service.get_position("BTCUSDT")
        if position:
            assert position.symbol == "BTCUSDT"
            assert isinstance(position.quantity, Decimal)

    async def test_place_order(self, binance_service: BinanceService):
        """주문 실행 테스트"""
        order_request = OrderRequest(
            symbol="BTCUSDT",
            side="BUY",
            quantity=Decimal("0.001"),
            leverage=10
        )
        
        order = await binance_service.place_order(order_request)
        assert order.symbol == "BTCUSDT"
        assert order.side == "BUY"
        assert order.status in ["NEW", "FILLED"]

    async def test_invalid_symbol(self, binance_service: BinanceService):
        """잘못된 심볼 테스트"""
        with pytest.raises(BinanceError):
            await binance_service.get_mark_price("INVALID")