from fastapi import APIRouter, HTTPException, Depends, WebSocket
from typing import List, Dict
from src.services.binance_service import BinanceService
from src.services.settings_service import SettingsService
from src.models.trading import OrderRequest
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1")
binance_service = BinanceService()
settings_service = SettingsService()

@router.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok"}

@router.get("/positions")
async def get_positions():
    """현재 포지션 조회"""
    try:
        positions = await binance_service.get_all_positions()  # get_positions -> get_all_positions
        return positions
    except Exception as e:
        logger.error(f"포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders")
async def create_order(order: OrderRequest):
    """주문 생성"""
    try:
        result = await binance_service.create_order(order)
        return result
    except Exception as e:
        logger.error(f"주문 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account")
async def get_account():
    """계정 정보 조회"""
    try:
        account = await binance_service.get_account_info()
        return account
    except Exception as e:
        logger.error(f"계정 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings():
    """현재 설정 조회"""
    try:
        settings = await settings_service.get_settings()
        return settings
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def update_settings(settings: Dict):
    """설정 업데이트"""
    try:
        await settings_service.update_settings(settings)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"설정 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exchange-info")
async def get_exchange_info():
    """거래소 정보 조회"""
    try:
        info = await binance_service.get_exchange_info()
        return info
    except Exception as e:
        logger.error(f"거래소 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))