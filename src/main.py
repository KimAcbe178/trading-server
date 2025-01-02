from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.models.trading import OrderRequest, Position
from src.services.binance_service import BinanceService
from src.services.notification_service import NotificationService
from src.services.settings_service import SettingsService
from src.services.websocket_manager import WebsocketManager
from src.utils.logger import logger, LoggerMixin
from src.utils.metrics import metrics
import psutil
import asyncio

# FastAPI 앱 초기화
app = FastAPI(
    title="Trading Server API",
    description="Binance Futures Trading Server",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 설정
api_router = APIRouter(prefix="/api/v1")

# 서비스 인스턴스 초기화
binance_service = BinanceService()
notification_service = NotificationService()
settings_service = SettingsService()
websocket_manager = WebsocketManager()

# 메트릭스 설정
metrics.setup_fastapi_metrics(app)

@api_router.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy"}

@api_router.get("/positions")
async def get_positions():
    """모든 포지션 조회"""
    try:
        positions = await binance_service.get_all_positions()
        return {"positions": positions}
    except Exception as e:
        logger.error(f"포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/positions/{symbol}")
async def get_position(symbol: str):
    """특정 심볼의 포지션 조회"""
    try:
        position = await binance_service.get_position(symbol)
        return {"position": position}
    except Exception as e:
        logger.error(f"{symbol} 포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/orders")
async def create_order(order_request: OrderRequest):
    """주문 생성"""
    try:
        order = await binance_service.place_order(order_request)
        await notification_service.send_trade_notification(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price
        )
        return {"order": order}
    except Exception as e:
        logger.error(f"주문 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/orders/{symbol}")
async def cancel_orders(symbol: str):
    """주문 취소"""
    try:
        await binance_service.cancel_all_orders(symbol)
        return {"message": f"{symbol} 모든 주문 취소 완료"}
    except Exception as e:
        logger.error(f"주문 취소 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/settings")
async def get_settings():
    """설정 조회"""
    try:
        settings = await settings_service.get_settings()
        return settings
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings")
async def update_settings(settings: dict):
    """설정 업데이트"""
    try:
        updated = await settings_service.update_settings(settings)
        return {"message": "설정 업데이트 완료", "settings": updated}
    except Exception as e:
        logger.error(f"설정 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.websocket("/ws")
async def websocket_endpoint(websocket):
    """웹소켓 엔드포인트"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.broadcast(data)
    except Exception as e:
        logger.error(f"웹소켓 에러: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

# 라우터 등록
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """서버 시작 이벤트"""
    logger.info("서버 시작")
    await binance_service.initialize()
    await notification_service.initialize()
    await settings_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 이벤트"""
    logger.info("서버 종료")
    await binance_service.cleanup()
    await notification_service.cleanup()
    await settings_service.cleanup()
    await websocket_manager.cleanup()