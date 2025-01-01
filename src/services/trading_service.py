from decimal import Decimal
from typing import Optional, List
from models.trading import Order, Position, OrderRequest
from services.binance_service import BinanceService
from services.settings_service import SettingsService
from services.notification_service import NotificationService
from utils.exceptions import ValidationError, PositionError
from utils.logger import logger

class TradingService:
    def __init__(
        self,
        binance_service: BinanceService,
        settings_service: SettingsService
    ):
        self.binance = binance_service
        self.settings = settings_service
        self.notification = NotificationService()
        self.positions: dict[str, Position] = {}

    async def initialize(self):
        """서비스 초기화"""
        try:
            # 바이낸스 클라이언트 초기화
            await self.binance.initialize()
            # 알림 서비스 초기화
            await self.notification.initialize()
            # 기존 포지션 로드
            await self._load_positions()
            logger.info("거래 서비스 초기화 완료")
            await self.notification.send_message("거래 서비스 시작", alert_level="SUCCESS")
            
        except Exception as e:
            logger.error(f"거래 서비스 초기화 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    async def _load_positions(self):
        """기존 포지션 로드"""
        try:
            positions = await self.binance.get_all_positions()
            self.positions = {pos.symbol: pos for pos in positions}
            logger.info(f"포지션 로드 완료: {len(positions)}개")
            
            if positions:
                # 기존 포지션 정보 알림
                for pos in positions:
                    await self.notification.send_position_update(
                        symbol=pos.symbol,
                        side=pos.side,
                        unrealized_pnl=float(pos.unrealized_pnl)
                    )
            
        except Exception as e:
            logger.error(f"포지션 로드 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    def _validate_order_request(self, request: OrderRequest):
        """주문 요청 유효성 검사"""
        # 심볼 검사
        if not self.settings.validate_symbol(request.symbol):
            raise ValidationError(f"유효하지 않은 심볼: {request.symbol}")
            
        # 레버리지 검사
        if not self.settings.validate_leverage(request.leverage):
            raise ValidationError(f"유효하지 않은 레버리지: {request.leverage}")
            
        # 수량 검사
        if not self.settings.validate_quantity(float(request.quantity)):
            raise ValidationError(f"유효하지 않은 수량: {request.quantity}")
            
        # 포지션 한도 검사
        trading_settings = self.settings.get_trading_settings()
        if (len(self.positions) >= trading_settings.max_positions and 
            request.symbol not in self.positions):
            raise PositionError(
                f"최대 포지션 한도 초과 (최대: {trading_settings.max_positions})"
            )

    async def place_order(self, request: OrderRequest) -> Order:
        """주문 실행"""
        try:
            # 주문 유효성 검사
            self._validate_order_request(request)
            
            # 주문 실행
            order = await self.binance.place_order(request)
            
            # 주문 실행 알림
            await self.notification.send_trade_notification(
                symbol=order.symbol,
                side=order.side,
                quantity=float(order.quantity),
                price=float(order.price)
            )
            
            # 포지션 업데이트
            if order.status == 'FILLED':
                position = await self.binance.get_position(request.symbol)
                if position:
                    self.positions[request.symbol] = position
                    # 포지션 업데이트 알림
                    await self.notification.send_position_update(
                        symbol=position.symbol,
                        side=position.side,
                        unrealized_pnl=float(position.unrealized_pnl)
                    )
                    
            logger.info(f"주문 실행 완료: {order.dict()}")
            return order
            
        except Exception as e:
            logger.error(f"주문 실행 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    async def close_position(self, symbol: str) -> Optional[Order]:
        """포지션 청산"""
        try:
            if symbol not in self.positions:
                raise PositionError(f"활성 포지션 없음: {symbol}")
            
            position = self.positions[symbol]
            
            # 포지션 청산
            order = await self.binance.close_position(symbol)
            
            if order and order.status == 'FILLED':
                # 청산 알림
                await self.notification.send_trade_notification(
                    symbol=symbol,
                    side="CLOSE",
                    quantity=float(position.quantity),
                    price=float(order.price),
                    pnl=float(position.unrealized_pnl)
                )
                
                # 포지션 제거
                del self.positions[symbol]
                
            # 관련된 대기 주문 취소
            await self.binance.cancel_all_orders(symbol)
            
            logger.info(f"포지션 청산 완료: {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"포지션 청산 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    async def get_position(self, symbol: str) -> Optional[Position]:
        """포지션 조회"""
        try:
            # 캐시된 포지션 반환
            if symbol in self.positions:
                # 최신 정보로 업데이트
                position = await self.binance.get_position(symbol)
                if position:
                    self.positions[symbol] = position
                    # 중요한 PnL 변동시 알림
                    if abs(float(position.unrealized_pnl)) > 100:  # $100 이상 변동
                        await self.notification.send_position_update(
                            symbol=position.symbol,
                            side=position.side,
                            unrealized_pnl=float(position.unrealized_pnl)
                        )
                return position
            return None
            
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    async def get_all_positions(self) -> List[Position]:
        """모든 포지션 조회"""
        try:
            # 모든 포지션 최신화
            positions = await self.binance.get_all_positions()
            self.positions = {pos.symbol: pos for pos in positions}
            return list(self.positions.values())
            
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            await self.notification.send_error_notification(e)
            raise

    async def update_position(self, symbol: str):
        """포지션 정보 업데이트"""
        try:
            position = await self.binance.get_position(symbol)
            if position:
                self.positions[symbol] = position
                # 중요한 PnL 변동시 알림
                if abs(float(position.unrealized_pnl)) > 100:  # $100 이상 변동
                    await self.notification.send_position_update(
                        symbol=position.symbol,
                        side=position.side,
                        unrealized_pnl=float(position.unrealized_pnl)
                    )
            elif symbol in self.positions:
                del self.positions[symbol]
                await self.notification.send_message(
                    f"포지션 종료: {symbol}",
                    alert_level="INFO"
                )
                
        except Exception as e:
            logger.error(f"포지션 업데이트 실패: {e}")
            await self.notification.send_error_notification(e)
            raise