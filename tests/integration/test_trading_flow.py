import pytest
import asyncio
from decimal import Decimal
from models.trading import OrderRequest
from services.trading_service import TradingService
from services.binance_service import BinanceService
from services.settings_service import SettingsService

@pytest.mark.integration
class TestTradingFlow:
    @pytest.fixture(autouse=True)
    async def setup(self, trading_service: TradingService):
        self.service = trading_service
        # 테스트 전 모든 포지션 청산
        positions = await self.service.get_all_positions()
        for position in positions:
            await self.service.close_position(position.symbol)

    @pytest.mark.asyncio
    async def test_complete_trading_flow(self):
        """전체 거래 흐름 테스트"""
        symbol = "BTCUSDT"
        
        # 1. 롱 포지션 진입
        long_order = await self.service.place_order(
            OrderRequest(
                symbol=symbol,
                side="BUY",
                quantity=Decimal("0.001"),
                leverage=10,
                stop_loss=Decimal("2"),  # 2% 손절
                take_profit=Decimal("2")  # 2% 익절
            )
        )
        assert long_order.status == "FILLED"
        
        # 포지션 확인
        position = await self.service.get_position(symbol)
        assert position is not None
        assert position.side == "LONG"
        
        # 2. 포지션 청산
        close_order = await self.service.close_position(symbol)
        assert close_order is not None
        
        # 포지션 제거 확인
        position = await self.service.get_position(symbol)
        assert position is None
        
        # 3. 숏 포지션 진입
        short_order = await self.service.place_order(
            OrderRequest(
                symbol=symbol,
                side="SELL",
                quantity=Decimal("0.001"),
                leverage=10
            )
        )
        assert short_order.status == "FILLED"
        
        # 포지션 확인
        position = await self.service.get_position(symbol)
        assert position is not None
        assert position.side == "SHORT"
        
        # 4. 최종 청산
        final_close = await self.service.close_position(symbol)
        assert final_close is not None

    @pytest.mark.asyncio
    async def test_multiple_position_management(self):
        """다중 포지션 관리 테스트"""
        symbols = ["BTCUSDT", "ETHUSDT"]
        orders = []
        
        # 여러 포지션 동시 진입
        for symbol in symbols:
            order = await self.service.place_order(
                OrderRequest(
                    symbol=symbol,
                    side="BUY",
                    quantity=Decimal("0.001"),
                    leverage=10
                )
            )
            orders.append(order)
        
        # 포지션 확인
        positions = await self.service.get_all_positions()
        assert len(positions) == len(symbols)
        
        # 모든 포지션 청산
        for symbol in symbols:
            await self.service.close_position(symbol)
        
        # 청산 확인
        positions = await self.service.get_all_positions()
        assert len(positions) == 0