import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.api.routes import router as api_router
from src.api.websocket import router as ws_router
from src.api.webhooks import router as webhook_router
from src.config.env import EnvConfig
from src.services.settings_service import SettingsService
from src.services.binance_service import BinanceService
from src.services.trading_service import TradingService
from src.services.websocket_manager import WebSocketManager
from src.utils.logger import logger
from src.utils.metrics import metrics_manager

# 서비스 초기화
settings_service = SettingsService()
binance_service = BinanceService()
trading_service = TradingService(settings_service, binance_service)
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    try:
        # Startup
        logger.info("서버 시작 중...")
        await settings_service._load_settings()
        await binance_service.initialize()
        await websocket_manager.initialize()
        logger.info("서버 초기화 완료")
        yield
    finally:
        # Shutdown
        logger.info("서버 종료 중...")
        await websocket_manager.cleanup()
        await binance_service.cleanup()
        await settings_service._save_settings()
        logger.info("서버 정상 종료됨")

# FastAPI 앱 초기화
app = FastAPI(
    title="WUYA Trading Server",
    description="암호화폐 자동 거래 서버",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=EnvConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 메트릭 설정
metrics_manager.setup_fastapi_metrics(app)

# 전역 서비스 의존성 설정
app.state.settings = settings_service
app.state.binance = binance_service
app.state.trading = trading_service
app.state.ws_manager = websocket_manager
app.state.metrics = metrics_manager

# 라우터 등록
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")
app.include_router(webhook_router, prefix="/webhooks")

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "binance_connected": binance_service.is_connected(),
        "active_websockets": websocket_manager.get_active_connections(),
        "trading_enabled": trading_service.is_enabled(),
        "memory_usage": metrics_manager.memory_usage._value.get()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭"""
    return {
        "websocket_connections": metrics_manager.active_connections._value.get(),
        "orders": {
            "total": metrics_manager.order_counter._value.get(),
            "by_symbol": {
                symbol: count for symbol, count in 
                metrics_manager.order_counter.collect()[0].samples
            }
        },
        "positions": {
            symbol: value for symbol, value in 
            metrics_manager.position_gauge.collect()[0].samples
        },
        "pnl": {
            symbol: value for symbol, value in 
            metrics_manager.pnl_gauge.collect()[0].samples
        },
        "api_latency": metrics_manager.api_latency._value.get(),
        "binance_requests": metrics_manager.binance_requests._value.get(),
        "memory_usage": metrics_manager.memory_usage._value.get()
    }

if __name__ == "__main__":
    import uvicorn
    
    # 개발 서버 설정
    uvicorn.run(
        "main:app",
        host=EnvConfig.SERVER_HOST,
        port=EnvConfig.SERVER_PORT,
        reload=EnvConfig.DEBUG,
        log_level="info"
    )