import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.models.settings import Settings, TradingSettings, APISettings
from src.utils.logger import logger, LoggerMixin
from src.utils.exceptions import ValidationError

class SettingsService(LoggerMixin):
    def __init__(self):
        self.settings_dir = Path("config")
        self.settings_file = self.settings_dir / "settings.json"
        self.settings: Optional[Settings] = None
        self._initialized = False

    async def initialize(self):
        """설정 서비스 초기화"""
        if self._initialized:
            return
            
        await self._load_settings()
        self._initialized = True
        self.logger.info("설정 서비스 초기화 완료")

    async def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized:
            await self.initialize()

    async def _load_settings(self):
        """설정 파일 로드"""
        try:
            self.settings_dir.mkdir(exist_ok=True)
            
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.settings = Settings.from_dict(data)
            else:
                # 기본 설정 생성
                self.settings = Settings()
                await self._save_settings()
                
            self.logger.info("설정 로드 완료")
            
        except Exception as e:
            self.logger.error(f"설정 로드 실패: {e}")
            raise ValidationError(f"설정 로드 실패: {str(e)}")

    async def _save_settings(self):
        """설정 파일 저장"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.dict(), f, indent=4, ensure_ascii=False)
            self.logger.info("설정 저장 완료")
            
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {e}")
            raise ValidationError(f"설정 저장 실패: {str(e)}")

    async def get_settings(self) -> Settings:
        """전체 설정 반환"""
        await self._ensure_initialized()
        return self.settings

    async def get_trading_settings(self) -> TradingSettings:
        """거래 설정 반환"""
        await self._ensure_initialized()
        return self.settings.trading

    async def get_api_settings(self) -> APISettings:
        """API 설정 반환"""
        await self._ensure_initialized()
        return self.settings.api

    async def update_trading_settings(self, settings: Dict[str, Any]):
        """거래 설정 업데이트"""
        await self._ensure_initialized()
        try:
            self.settings.trading = TradingSettings(**settings)
            await self._save_settings()
            self.logger.info("거래 설정 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"거래 설정 업데이트 실패: {e}")
            raise ValidationError(f"거래 설정 업데이트 실패: {str(e)}")

    async def update_api_settings(self, settings: Dict[str, Any]):
        """API 설정 업데이트"""
        await self._ensure_initialized()
        try:
            self.settings.api = APISettings(**settings)
            await self._save_settings()
            self.logger.info("API 설정 업데이트 완료")
            
        except Exception as e:
            self.logger.error(f"API 설정 업데이트 실패: {e}")
            raise ValidationError(f"API 설정 업데이트 실패: {str(e)}")

    def validate_symbol(self, symbol: str) -> bool:
        """심볼 유효성 검사"""
        if not self.settings:
            raise ValidationError("설정이 초기화되지 않았습니다")
        return symbol in self.settings.trading.allowed_symbols

    def validate_leverage(self, leverage: int) -> bool:
        """레버리지 유효성 검사"""
        return 1 <= leverage <= 125

    def validate_quantity(self, quantity: float) -> bool:
        """주문 수량 유효성 검사"""
        return quantity > 0

    async def cleanup(self):
        """리소스 정리"""
        if self._initialized:
            await self._save_settings()
            self._initialized = False
            self.logger.info("설정 서비스 정리 완료")