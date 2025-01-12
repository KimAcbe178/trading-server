from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from src.services.websocket_manager import WebSocketManager  # import 경로 수정
from src.services.binance_service import BinanceService     # import 경로 수정
from src.utils.logger import logger                         # import 경로 수정
from src.utils.metrics import metrics_manager                 # import 경로 수정

router = APIRouter()
ws_manager = WebSocketManager()
binance_service = BinanceService()

class WebSocketConnection:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.subscribed_symbols: Set[str] = set()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = WebSocketConnection(websocket)
    metrics.active_connections.inc()  # 연결 수 증가
    
    try:
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_json()
                
                # 메시지 타입에 따른 처리
                message_type = data.get('type')
                if message_type == 'subscribe':
                    symbol = data.get('symbol')
                    if symbol:
                        connection.subscribed_symbols.add(symbol)
                        asyncio.create_task(
                            start_market_updates(connection, symbol)
                        )
                        logger.info(f"심볼 구독 시작: {symbol}")
                        # 구독 성공 응답
                        await websocket.send_json({
                            'type': 'subscribed',
                            'symbol': symbol
                        })
                        
                elif message_type == 'unsubscribe':
                    symbol = data.get('symbol')
                    if symbol in connection.subscribed_symbols:
                        connection.subscribed_symbols.remove(symbol)
                        logger.info(f"심볼 구독 취소: {symbol}")
                        # 구독 취소 성공 응답
                        await websocket.send_json({
                            'type': 'unsubscribed',
                            'symbol': symbol
                        })
                        
            except json.JSONDecodeError:
                logger.error("잘못된 JSON 형식")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket 연결 종료")
        
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
        
    finally:
        # 연결 종료 시 정리
        metrics.active_connections.dec()  # 연결 수 감소
        for symbol in connection.subscribed_symbols:
            await ws_manager.disconnect(websocket, symbol)

async def start_market_updates(connection: WebSocketConnection, symbol: str):
    """실시간 시장 데이터 업데이트"""
    try:
        while symbol in connection.subscribed_symbols:
            try:
                # 현재가 조회
                price = await binance_service.get_mark_price(symbol)
                
                # 클라이언트로 데이터 전송
                await connection.websocket.send_json({
                    'type': 'price',
                    'data': {
                        'symbol': symbol,
                        'price': str(price)
                    }
                })
                
                # 1초 대기
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"가격 업데이트 오류: {e}")
                await asyncio.sleep(5)  # 오류 발생 시 더 긴 대기
            
    except Exception as e:
        logger.error(f"시장 데이터 업데이트 오류: {e}")
        if symbol in connection.subscribed_symbols:
            connection.subscribed_symbols.remove(symbol)