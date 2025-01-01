import json
from pathlib import Path
from typing import Optional
from models.settings import Settings, TradingSettings, APISettings
from utils.exceptions import ValidationError
from utils.logger import logger

class SettingsService:
    def __init__(self):
        self.settings_dir = Path("config")
        self.settings_file = self.settings_dir / "settings.json"
        self.settings: Optional[Settings] = None
        self._load_settings()

    def _load_settings(self):
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
                self._save_settings()
                
            logger.info("설정 로드 완료")
            
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            raise ValidationError(f"설정 로드 실패: {str(e)}")

    def _save_settings(self):
        """설정 파일 저장"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.dict(), f, indent=4)
            logger.info("설정 저장 완료")
            
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
            raise ValidationError(f"설정 저장 실패: {str(e)}")

    def get_settings(self) -> Settings:
        """전체 설정 반환"""
        return self.settings

    def get_trading_settings(self) -> TradingSettings:
        """거래 설정 반환"""
        return self.settings.trading

    def get_api_settings(self) -> APISettings:
        """API 설정 반환"""
        return self.settings.api

    def update_trading_settings(self, settings: dict):
        """거래 설정 업데이트"""
        try:
            self.settings.trading = TradingSettings(**settings)
            self._save_settings()
            logger.info("거래 설정 업데이트 완료")
            
        except Exception as e:
            logger.error(f"거래 설정 업데이트 실패: {e}")
            raise ValidationError(f"거래 설정 업데이트 실패: {str(e)}")

    def update_api_settings(self, settings: dict):
        """API 설정 업데이트"""
        try:
            self.settings.api = APISettings(**settings)
            self._save_settings()
            logger.info("API 설정 업데이트 완료")
            
        except Exception as e:
            logger.error(f"API 설정 업데이트 실패: {e}")
            raise ValidationError(f"API 설정 업데이트 실패: {str(e)}")

    def validate_symbol(self, symbol: str) -> bool:
        """심볼 유효성 검사"""
        return symbol in self.settings.trading.allowed_symbols

    def validate_leverage(self, leverage: int) -> bool:
        """레버리지 유효성 검사"""
        return 1 <= leverage <= 125

    def validate_quantity(self, quantity: float) -> bool:
        """주문 수량 유효성 검사"""
        return quantity > 0