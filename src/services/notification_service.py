from telegram.ext import ApplicationBuilder
from telegram.error import TelegramError
from config.env import EnvConfig
from utils.logger import logger
from typing import List, Optional
import asyncio

class NotificationService:
    def __init__(self):
        self.bot = None
        self.chat_ids: List[str] = []
        self._initialized = False

    async def initialize(self):
        """텔레그램 봇 초기화"""
        if self._initialized:
            return

        try:
            self.bot = await ApplicationBuilder().token(
                EnvConfig.TELEGRAM_BOT_TOKEN
            ).build()
            self.chat_ids = EnvConfig.TELEGRAM_CHAT_IDS.split(',')
            self._initialized = True
            logger.info("텔레그램 봇 초기화 완료")
            
        except Exception as e:
            logger.error(f"텔레그램 봇 초기화 실패: {e}")
            raise

    async def send_message(
        self, 
        message: str, 
        chat_id: Optional[str] = None,
        alert_level: str = "INFO"
    ):
        """메시지 전송"""
        if not self._initialized:
            await self.initialize()

        # 알림 레벨에 따른 이모지 설정
        emoji_map = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "🚨",
            "TRADE": "💰"
        }
        emoji = emoji_map.get(alert_level, "ℹ️")
        formatted_message = f"{emoji} {message}"

        try:
            if chat_id:
                await self.bot.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message
                )
            else:
                # 모든 등록된 채팅방에 전송
                for cid in self.chat_ids:
                    await self.bot.bot.send_message(
                        chat_id=cid,
                        text=formatted_message
                    )
                    # 텔레그램 API 제한 방지를 위한 딜레이
                    await asyncio.sleep(0.1)
                    
        except TelegramError as e:
            logger.error(f"텔레그램 메시지 전송 실패: {e}")
            raise

    async def send_trade_notification(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float,
        pnl: Optional[float] = None
    ):
        """거래 알림 전송"""
        message = (
            f"거래 실행: {symbol}\n"
            f"방향: {side}\n"
            f"수량: {quantity}\n"
            f"가격: {price:,.2f} USDT"
        )
        
        if pnl is not None:
            message += f"\nPnL: {pnl:,.2f} USDT"
            
        await self.send_message(message, alert_level="TRADE")

    async def send_error_notification(self, error: Exception):
        """에러 알림 전송"""
        message = f"에러 발생:\n{str(error)}"
        await self.send_message(message, alert_level="ERROR")

    async def send_position_update(
        self, 
        symbol: str, 
        side: str, 
        unrealized_pnl: float
    ):
        """포지션 업데이트 알림"""
        message = (
            f"포지션 업데이트: {symbol}\n"
            f"방향: {side}\n"
            f"미실현 손익: {unrealized_pnl:,.2f} USDT"
        )
        await self.send_message(message, alert_level="INFO")