import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from config.env import EnvConfig

class CustomFormatter(logging.Formatter):
    """커스텀 로그 포매터"""
    
    # ANSI 이스케이프 코드를 사용한 색상 정의
    COLORS = {
        'DEBUG': '\033[36m',    # CYAN
        'INFO': '\033[32m',     # GREEN
        'WARNING': '\033[33m',  # YELLOW
        'ERROR': '\033[31m',    # RED
        'CRITICAL': '\033[41m', # RED BACKGROUND
    }
    RESET = '\033[0m'

    def __init__(self, use_colors: bool = True):
        super().__init__(
            fmt='[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors

    def format(self, record):
        # 원본 메시지 포맷
        formatted = super().format(record)
        
        if self.use_colors and record.levelname in self.COLORS:
            # 로그 레벨에 색상 적용
            color = self.COLORS[record.levelname]
            formatted = f"{color}{formatted}{self.RESET}"
            
        return formatted

def setup_logger(name: str = 'wuya_server') -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있다면 스킵
    if logger.handlers:
        return logger
        
    # 로그 레벨 설정
    logger.setLevel(getattr(logging, EnvConfig.LOG_LEVEL))
    
    # 로그 디렉토리 생성
    log_dir = Path(EnvConfig.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 일반 로그 파일 핸들러 (10MB 단위로 로테이션)
    general_handler = RotatingFileHandler(
        filename=log_dir / 'server.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # 에러 로그 파일 핸들러 (매일 자정에 로테이션)
    error_handler = TimedRotatingFileHandler(
        filename=log_dir / 'error.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d]\n'
        'Message: %(message)s\n'
        'Exception: %(exc_info)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if EnvConfig.DEBUG else logging.INFO)
    console_handler.setFormatter(CustomFormatter(use_colors=True))
    
    # 핸들러 추가
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """로거 인스턴스 반환"""
    if name:
        return logging.getLogger(f"wuya_server.{name}")
    return logging.getLogger("wuya_server")

# 기본 로거 설정
logger = setup_logger()

class LoggerMixin:
    """로깅 기능을 제공하는 믹스인 클래스"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

def log_exception(logger: logging.Logger):
    """예외 로깅 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator