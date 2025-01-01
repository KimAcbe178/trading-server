from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException
from decimal import Decimal
from typing import Optional, Dict, Any
from config.env import EnvConfig
from models.trading import Order, Position, OrderRequest
from utils.exceptions import BinanceError
from utils.logger import logger

class BinanceService:
    def __init__(self):
        self.client = None
        self._initialized = False

    async def initialize(self):
        """바이낸스 클라이언트 초기화"""
        if self._initialized:
            return

        try:
            self.client = await AsyncClient.create(
                api_key=EnvConfig.BINANCE_API_KEY,
                api_secret=EnvConfig.BINANCE_API_SECRET,
                testnet=EnvConfig.USE_TESTNET
            )
            self._initialized = True
            logger.info("바이낸스 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"바이낸스 클라이언트 초기화 실패: {e}")
            raise BinanceError(str(e))

    async def cleanup(self):
        """리소스 정리"""
        if self.client:
            await self.client.close_connection()
            self._initialized = False
            logger.info("바이낸스 연결 종료")

    async def _ensure_initialized(self):
        """클라이언트 초기화 확인"""
        if not self._initialized:
            await self.initialize()

    async def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """거래소 정보 조회"""
        await self._ensure_initialized()
        try:
            if symbol:
                return await self.client.futures_exchange_info(symbol=symbol)
            return await self.client.futures_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"거래소 정보 조회 실패: {e}")
            raise BinanceError(str(e))

    async def get_mark_price(self, symbol: str) -> Decimal:
        """마크 가격 조회"""
        await self._ensure_initialized()
        try:
            price_data = await self.client.futures_mark_price(symbol=symbol)
            return Decimal(str(price_data['markPrice']))
        except BinanceAPIException as e:
            logger.error(f"마크 가격 조회 실패: {e}")
            raise BinanceError(str(e))

    async def get_position(self, symbol: str) -> Optional[Position]:
        """포지션 정보 조회"""
        await self._ensure_initialized()
        try:
            positions = await self.client.futures_position_information(symbol=symbol)
            position_data = positions[0] if positions else None
            
            if position_data and float(position_data['positionAmt']) != 0:
                return Position.from_binance(position_data)
            return None
            
        except BinanceAPIException as e:
            logger.error(f"포지션 정보 조회 실패: {e}")
            raise BinanceError(str(e))

    async def get_all_positions(self) -> list[Position]:
        """모든 포지션 조회"""
        await self._ensure_initialized()
        try:
            positions = await self.client.futures_position_information()
            return [
                Position.from_binance(pos) 
                for pos in positions 
                if float(pos['positionAmt']) != 0
            ]
        except BinanceAPIException as e:
            logger.error(f"포지션 조회 실패: {e}")
            raise BinanceError(str(e))

    async def place_order(self, order_request: OrderRequest) -> Order:
        """주문 실행"""
        await self._ensure_initialized()
        try:
            # 레버리지 설정
            await self.client.futures_change_leverage(
                symbol=order_request.symbol,
                leverage=order_request.leverage
            )
            
            # 기본 주문 파라미터
            order_params = {
                "symbol": order_request.symbol,
                "side": order_request.side,
                "type": "MARKET",
                "quantity": float(order_request.quantity)
            }
            
            # 주문 실행
            order_result = await self.client.futures_create_order(**order_params)
            
            # 스탑로스/익절 주문 설정
            if order_request.stop_loss or order_request.take_profit:
                await self._set_sl_tp(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    stop_loss=order_request.stop_loss,
                    take_profit=order_request.take_profit
                )
            
            return Order.from_binance(order_result)
            
        except BinanceAPIException as e:
            logger.error(f"주문 실패: {e}")
            raise BinanceError(str(e))

    async def _set_sl_tp(
        self, 
        symbol: str, 
        side: str, 
        quantity: Decimal,
        stop_loss: Optional[Decimal],
        take_profit: Optional[Decimal]
    ):
        """스탑로스/익절 주문 설정"""
        try:
            current_price = await self.get_mark_price(symbol)
            
            if stop_loss:
                sl_params = {
                    "symbol": symbol,
                    "side": "SELL" if side == "BUY" else "BUY",
                    "type": "STOP_MARKET",
                    "quantity": float(quantity),
                    "stopPrice": float(current_price * (1 - stop_loss/100) 
                                    if side == "BUY" 
                                    else current_price * (1 + stop_loss/100))
                }
                await self.client.futures_create_order(**sl_params)
            
            if take_profit:
                tp_params = {
                    "symbol": symbol,
                    "side": "SELL" if side == "BUY" else "BUY",
                    "type": "TAKE_PROFIT_MARKET",
                    "quantity": float(quantity),
                    "stopPrice": float(current_price * (1 + take_profit/100) 
                                    if side == "BUY" 
                                    else current_price * (1 - take_profit/100))
                }
                await self.client.futures_create_order(**tp_params)
                
        except BinanceAPIException as e:
            logger.error(f"SL/TP 설정 실패: {e}")
            raise BinanceError(str(e))

    async def close_position(self, symbol: str) -> Optional[Order]:
        """포지션 청산"""
        await self._ensure_initialized()
        try:
            position = await self.get_position(symbol)
            if not position:
                return None
                
            close_params = {
                "symbol": symbol,
                "side": "SELL" if position.side == "LONG" else "BUY",
                "type": "MARKET",
                "quantity": float(position.quantity)
            }
            
            result = await self.client.futures_create_order(**close_params)
            return Order.from_binance(result)
            
        except BinanceAPIException as e:
            logger.error(f"포지션 청산 실패: {e}")
            raise BinanceError(str(e))

    async def cancel_all_orders(self, symbol: str):
        """모든 대기 주문 취소"""
        await self._ensure_initialized()
        try:
            await self.client.futures_cancel_all_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            logger.error(f"주문 취소 실패: {e}")
            raise BinanceError(str(e))