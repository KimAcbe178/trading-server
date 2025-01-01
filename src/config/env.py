import os
from dotenv import load_dotenv
from pathlib import Path

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
    USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() == 'true'
    
    # 데이터베이스 설정
    DB_URL = os.getenv('DB_URL', 'sqlite:///./trading.db')
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # 웹훅 설정
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')
    
    @classmethod
    def validate(cls):
        """필수 환경 변수 검증"""
        required_vars = [
            'BINANCE_API_KEY',
            'BINANCE_API_SECRET'
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
    # 텔레그램 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS', '')