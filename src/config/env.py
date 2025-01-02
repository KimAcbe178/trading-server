import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class EnvConfig:
    # 기본 설정
    ENV = os.getenv('ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 서버 설정
    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '8000'))
    
    # 바이낸스 API 설정
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    USE_TESTNET = os.getenv('USE_TESTNET', 'False').lower() == 'true'  # 기본값을 False로 변경
    
    # 데이터베이스 설정
    DB_URL = os.getenv('DB_URL', 'sqlite:///./trading.db')
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 
        '[%(asctime)s] %(levelname)s [%(name)s:%(funcName)s] %(message)s'
    )
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # 웹훅 설정
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')
    
    # 텔레그램 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # 단일 채팅 ID 추가
    TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS', '').split(',') if os.getenv('TELEGRAM_CHAT_IDS') else []
    
    # 거래 설정
    DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', '10'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '1000'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2.0'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4.0'))
    
    @classmethod
    def validate(cls):
        """필수 환경 변수 검증"""
        required_vars = [
            ('BINANCE_API_KEY', cls.BINANCE_API_KEY),
            ('BINANCE_API_SECRET', cls.BINANCE_API_SECRET),
        ]
        
        # 텔레그램 설정이 있는 경우 추가 검증
        if cls.TELEGRAM_BOT_TOKEN:
            required_vars.append(('TELEGRAM_CHAT_ID', cls.TELEGRAM_CHAT_ID))
        
        missing = [var_name for var_name, var_value in required_vars if not var_value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def get_telegram_chat_ids(cls) -> List[str]:
        """텔레그램 채팅 ID 목록 반환"""
        if cls.TELEGRAM_CHAT_ID:
            return [cls.TELEGRAM_CHAT_ID] + cls.TELEGRAM_CHAT_IDS
        return cls.TELEGRAM_CHAT_IDS
    
    @classmethod
    def is_development(cls) -> bool:
        """개발 환경 여부 확인"""
        return cls.ENV == 'development'
    
    @classmethod
    def is_production(cls) -> bool:
        """운영 환경 여부 확인"""
        return cls.ENV == 'production'

# 환경 변수 검증
EnvConfig.validate()