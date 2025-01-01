from fastapi import APIRouter, Header, HTTPException, Request
from typing import Optional
from services.trading_service import TradingService
from config.env import EnvConfig
from utils.logger import logger
import hmac
import hashlib

router = APIRouter()

def verify_webhook_signature(
    signature: str, 
    timestamp: str, 
    body: bytes
) -> bool:
    """웹훅 서명 검증"""
    if not EnvConfig.WEBHOOK_SECRET:
        return False
        
    # 서명 생성
    message = f"{timestamp}{body.decode()}"
    expected_signature = hmac.new(
        EnvConfig.WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@router.post("/webhook/binance")
async def binance_webhook(
    request: Request,
    x_binance_signature: Optional[str] = Header(None),
    x_binance_timestamp: Optional[str] = Header(None)
):
    """바이낸스 웹훅 처리"""
    try:
        # 요청 본문 읽기
        body = await request.body()
        
        # 서명 검증
        if not verify_webhook_signature(
            x_binance_signature, 
            x_binance_timestamp, 
            body
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        # 웹훅 데이터 파싱
        data = await request.json()
        event_type = data.get('e')
        
        # 이벤트 타입별 처리
        if event_type == 'ORDER_TRADE_UPDATE':
            await handle_order_update(data)
        elif event_type == 'ACCOUNT_UPDATE':
            await handle_account_update(data)
            
        return {"message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"웹훅 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_order_update(data: dict):
    """주문 업데이트 처리"""
    try:
        order_data = data.get('o', {})
        symbol = order_data.get('s')
        
        if symbol:
            # 포지션 정보 업데이트
            await trading_service.update_position(symbol)
            
        logger.info(f"주문 업데이트 처리 완료: {symbol}")
        
    except Exception as e:
        logger.error(f"주문 업데이트 처리 실패: {e}")
        raise

async def handle_account_update(data: dict):
    """계정 업데이트 처리"""
    try:
        # 포지션 변경 확인
        positions = data.get('a', {}).get('P', [])
        
        for pos in positions:
            symbol = pos.get('s')
            if symbol:
                # 포지션 정보 업데이트
                await trading_service.update_position(symbol)
                
        logger.info(f"계정 업데이트 처리 완료: {len(positions)}개 포지션")
        
    except Exception as e:
        logger.error(f"계정 업데이트 처리 실패: {e}")
        raise