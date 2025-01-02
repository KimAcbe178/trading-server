from binance.client import Client
from binance.exceptions import BinanceAPIException
from decimal import Decimal
from typing import Optional, Dict, Any, List
from src.config.env import EnvConfig
from src.models.trading import Order, Position, OrderRequest
from src.utils.exceptions import BinanceError
from src.utils.logger import logger, LoggerMixin

class BinanceService(LoggerMixin):
    def __init__(self):
        self.client = None
        self._initialized = False
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, List[Order]] = {}

    async def initialize(self):
        """바이낸스 클라이언트 초기화"""
        if self._initialized:
            return

        try:
            self.client = Client(
                api_key=EnvConfig.BINANCE_API_KEY,
                api_secret=EnvConfig.BINANCE_API_SECRET,
                testnet=False  # 실제 바이낸스 사용
            )
            
            # API 테스트
            try:
                # 선물 계정 정보 확인
                account = self.client.futures_account()
                self.logger.info("선물 계정 접근 권한 확인 완료")
                self.logger.info(f"계정 정보: {account['totalWalletBalance']} USDT")
                
            except BinanceAPIException as e:
                self.logger.error(f"API 테스트 실패 (code: {e.code}): {e.message}")
                raise
            
            self._initialized = True
            self.logger.info("바이낸스 클라이언트 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"바이낸스 클라이언트 초기화 실패: {e}")
            raise

    async def _ensure_initialized(self):
        """클라이언트 초기화 확인"""
        if not self._initialized:
            await self.initialize()

    async def update_positions(self):
        """포지션 정보 업데이트"""
        await self._ensure_initialized()
        
        try:
            positions = self.client.futures_position_information()
            self.positions = {
                p['symbol']: Position.from_binance(p)
                for p in positions
                if float(p['positionAmt']) != 0
            }
            self.logger.info(f"포지션 업데이트 완료: {len(self.positions)} 개의 활성 포지션")
            
        except BinanceAPIException as e:
            self.logger.error(f"포지션 업데이트 실패: {e}")
            raise BinanceError(f"포지션 업데이트 실패: {e}")

    async def get_all_positions(self) -> List[Position]:
        """모든 포지션 조회"""
        await self._ensure_initialized()
        await self.update_positions()
        return list(self.positions.values())

    async def get_position(self, symbol: str) -> Optional[Position]:
        """특정 심볼의 포지션 조회"""
        await self._ensure_initialized()
        
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            if positions and float(positions[0]['positionAmt']) != 0:
                position = Position.from_binance(positions[0])
                self.positions[symbol] = position
                return position
            return None
        except BinanceAPIException as e:
            self.logger.error(f"{symbol} 포지션 조회 실패: {e}")
            raise BinanceError(f"{symbol} 포지션 조회 실패: {e}")

    async def place_order(self, order_request: OrderRequest) -> Order:
        """주문 실행"""
        await self._ensure_initialized()
        
        try:
            # 레버리지 설정
            self.client.futures_change_leverage(
                symbol=order_request.symbol,
                leverage=order_request.leverage
            )

            # 주문 실행
            order = self.client.futures_create_order(
                symbol=order_request.symbol,
                side=order_request.side,
                type='MARKET',
                quantity=order_request.quantity
            )
            
            # 주문 기록 업데이트
            if order_request.symbol not in self.orders:
                self.orders[order_request.symbol] = []
            self.orders[order_request.symbol].append(Order.from_binance(order))
            
            # 포지션 업데이트
            await self.update_positions()
            
            return Order.from_binance(order)
            
        except BinanceAPIException as e:
            self.logger.error(f"주문 실패: {e}")
            raise BinanceError(f"주문 실패: {e}")

    async def cancel_all_orders(self, symbol: str):
        """모든 주문 취소"""
        await self._ensure_initialized()
        
        try:
            self.client.futures_cancel_all_open_orders(symbol=symbol)
            if symbol in self.orders:
                self.orders[symbol] = []
            self.logger.info(f"{symbol} 모든 주문 취소 완료")
        except BinanceAPIException as e:
            self.logger.error(f"주문 취소 실패: {e}")
            raise BinanceError(f"주문 취소 실패: {e}")

    async def get_order_history(self, symbol: str) -> List[Order]:
        """주문 내역 조회"""
        await self._ensure_initialized()
        return self.orders.get(symbol, [])

    async def cleanup(self):
        """리소스 정리"""
        if self.client:
            self.client.close_connection()
            self._initialized = False
            self.positions.clear()
            self.orders.clear()
            self.logger.info("바이낸스 클라이언트 연결 종료")