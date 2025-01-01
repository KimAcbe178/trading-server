from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models.trading import OrderRequest, Order, Position
from models.settings import Settings, TradingSettings, APISettings
from services.trading_service import TradingService
from services.settings_service import SettingsService
from services.binance_service import BinanceService
from utils.exceptions import TradingException
from utils.logger import logger

router = APIRouter()

# 서비스 인스턴스
settings_service = SettingsService()
binance_service = BinanceService()
trading_service = TradingService(binance_service, settings_service)

@router.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    await trading_service.initialize()

@router.get("/settings", response_model=Settings)
async def get_settings():
    """전체 설정 조회"""
    try:
        return settings_service.get_settings()
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/settings/trading")
async def update_trading_settings(settings: TradingSettings):
    """거래 설정 업데이트"""
    try:
        settings_service.update_trading_settings(settings.dict())
        return {"message": "거래 설정 업데이트 완료"}
    except Exception as e:
        logger.error(f"거래 설정 업데이트 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/settings/api")
async def update_api_settings(settings: APISettings):
    """API 설정 업데이트"""
    try:
        settings_service.update_api_settings(settings.dict())
        return {"message": "API 설정 업데이트 완료"}
    except Exception as e:
        logger.error(f"API 설정 업데이트 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/market/price/{symbol}")
async def get_mark_price(symbol: str):
    """마크 가격 조회"""
    try:
        price = await binance_service.get_mark_price(symbol)
        return {"symbol": symbol, "price": str(price)}
    except TradingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"가격 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trading/order", response_model=Order)
async def place_order(order_request: OrderRequest):
    """주문 실행"""
    try:
        order = await trading_service.place_order(order_request)
        return order
    except TradingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"주문 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/positions", response_model=List[Position])
async def get_all_positions():
    """모든 포지션 조회"""
    try:
        return await trading_service.get_all_positions()
    except TradingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/position/{symbol}", response_model=Optional[Position])
async def get_position(symbol: str):
    """특정 심볼의 포지션 조회"""
    try:
        return await trading_service.get_position(symbol)
    except TradingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trading/close-position/{symbol}")
async def close_position(symbol: str):
    """포지션 청산"""
    try:
        order = await trading_service.close_position(symbol)
        if order:
            return {"message": "포지션 청산 완료", "order": order}
        return {"message": "활성 포지션 없음"}
    except TradingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.error(f"포지션 청산 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))