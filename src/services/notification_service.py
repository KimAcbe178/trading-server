from telegram import Bot
from src.config.env import EnvConfig
from src.utils.logger import logger, LoggerMixin

class NotificationService(LoggerMixin):
    def __init__(self):
        self.bot = None
        self._initialized = False
        self.enabled = bool(getattr(EnvConfig, 'TELEGRAM_BOT_TOKEN', None) and 
                          getattr(EnvConfig, 'TELEGRAM_CHAT_ID', None))

    async def initialize(self):
        """텔레그램 봇 초기화"""
        if self._initialized:
            return
            
        if not self.enabled:
            self.logger.info("텔레그램 알림 비활성화")
            return

        try:
            # 텔레그램 봇 생성
            self.bot = Bot(token=EnvConfig.TELEGRAM_BOT_TOKEN)
            
            # 봇 테스트
            await self.bot.get_me()
            
            self._initialized = True
            self.logger.info("텔레그램 봇 초기화 완료")
            
            # 시작 메시지 전송
            await self.send_message("Trading Server Started")
            
        except Exception as e:
            self.logger.error(f"텔레그램 봇 초기화 실패: {e}")
            raise

    async def _ensure_initialized(self):
        """봇 초기화 확인"""
        if not self._initialized and self.enabled:
            await self.initialize()

    async def send_message(self, message: str):
        """메시지 전송"""
        if not self.enabled:
            self.logger.debug(f"텔레그램 알림 비활성화 상태에서 메시지 시도: {message}")
            return
            
        await self._ensure_initialized()
        
        try:
            await self.bot.send_message(
                chat_id=EnvConfig.TELEGRAM_CHAT_ID,
                text=message
            )
            self.logger.info(f"텔레그램 메시지 전송 완료: {message}")
        except Exception as e:
            self.logger.error(f"텔레그램 메시지 전송 실패: {e}")
            raise

    async def cleanup(self):
        """리소스 정리"""
        if self.bot and self._initialized:
            self._initialized = False
            self.bot = None
            self.logger.info("텔레그램 봇 연결 종료")