from fastapi import APIRouter, HTTPException
from models.trading import OrderRequest, Position
from services.binance_service import BinanceService
from utils.logger import logger
from utils.metrics import metrics
import psutil
import asyncio

app = FastAPI()
metrics.setup_fastapi_metrics(app)

async def update_system_metrics():
    """시스템 메트릭 주기적 업데이트"""
    while True:
        process = psutil.Process()
        metrics.memory_usage.set(process.memory_info().rss)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_system_metrics())

router = APIRouter()
binance_service = BinanceService()

@router.get("/market/price/{symbol}")
async def get_symbol_price(symbol: str):
    """심볼 현재가 조회"""
    try:
        price = await binance_service.get_symbol_price(symbol)
        return {"symbol": symbol, "price": price}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/trading/order")
async def place_order(order: OrderRequest):
    """주문 실행"""
    try:
        # 레버리지 설정
        await binance_service.set_leverage(
            order.symbol, 
            order.leverage
        )
        
        # 주문 실행
        result = await binance_service.place_order({
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trading/positions/{symbol}")
async def get_position(symbol: str):
    """포지션 정보 조회"""
    try:
        position = await binance_service.get_position(symbol)
        if position:
            return Position.from_binance(position)
        raise HTTPException(status_code=404, detail="포지션을 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/trading/close-position/{symbol}")
async def close_position(symbol: str):
    """포지션 청산"""
    try:
        result = await binance_service.close_position(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))