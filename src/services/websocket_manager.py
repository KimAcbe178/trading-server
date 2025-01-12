from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from utils.logger import logger

class WebSocketManager:
    def __init__(self):
        # 심볼별 활성 연결 관리
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        logger.info("WebSocket 매니저 초기화 완료")

    async def connect(self, websocket: WebSocket, symbol: str = "BTCUSDT"):
        """새로운 WebSocket 연결 처리"""
        try:
            # WebSocket 연결 수락
            await websocket.accept()
            
            async with self._lock:
                # 심볼에 대한 연결 세트가 없으면 생성
                if symbol not in self.active_connections:
                    self.active_connections[symbol] = set()
                    
                # 연결 추가
                self.active_connections[symbol].add(websocket)
                
            logger.info(f"새로운 WebSocket 연결 수락됨 (symbol: {symbol}, 총 연결: {len(self.active_connections[symbol])})")
            
            # 연결 성공 메시지 전송
            await self.send_personal_message(
                {
                    "type": "connection",
                    "status": "connected",
                    "symbol": symbol,
                    "message": "WebSocket 연결이 성공적으로 설정되었습니다."
                },
                websocket
            )
            
        except Exception as e:
            logger.error(f"WebSocket 연결 중 오류 발생: {e}")
            if websocket in self.active_connections.get(symbol, set()):
                await self.disconnect(websocket, symbol)
            raise

    async def disconnect(self, websocket: WebSocket, symbol: str):
        """WebSocket 연결 종료 처리"""
        try:
            async with self._lock:
                if symbol in self.active_connections:
                    # 연결 제거
                    self.active_connections[symbol].discard(websocket)
                    logger.info(f"WebSocket 연결 종료됨 (symbol: {symbol}, 남은 연결: {len(self.active_connections[symbol])})")
                    
                    # 해당 심볼의 마지막 연결이 종료되면 세트 제거
                    if not self.active_connections[symbol]:
                        del self.active_connections[symbol]
                        logger.info(f"심볼 {symbol}의 모든 연결이 종료됨")
                
        except Exception as e:
            logger.error(f"WebSocket 연결 종료 중 오류 발생: {e}")

    async def broadcast(self, message: dict, symbol: str):
        """특정 심볼을 구독 중인 모든 클라이언트에 메시지 전송"""
        if symbol not in self.active_connections:
            return

        disconnected = set()
        
        for connection in self.active_connections[symbol].copy():  # 복사본으로 순회
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
                logger.warning(f"브로드캐스트 중 연결 끊김 감지 (symbol: {symbol})")
            except Exception as e:
                logger.error(f"브로드캐스트 중 오류 발생: {e}")
                disconnected.add(connection)

        # 끊어진 연결 제거
        if disconnected:
            async with self._lock:
                self.active_connections[symbol] -= disconnected
                logger.info(f"끊어진 연결 제거됨 (symbol: {symbol}, 제거된 연결: {len(disconnected)})")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 클라이언트에 메시지 전송"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"개별 메시지 전송 중 오류 발생: {e}")
            raise

    async def change_symbol(self, websocket: WebSocket, old_symbol: str, new_symbol: str):
        """클라이언트의 구독 심볼 변경"""
        try:
            async with self._lock:
                # 이전 심볼에서 연결 제거
                if old_symbol in self.active_connections:
                    self.active_connections[old_symbol].discard(websocket)
                    if not self.active_connections[old_symbol]:
                        del self.active_connections[old_symbol]
                
                # 새 심볼에 연결 추가
                if new_symbol not in self.active_connections:
                    self.active_connections[new_symbol] = set()
                self.active_connections[new_symbol].add(websocket)
            
            logger.info(f"심볼 변경됨: {old_symbol} -> {new_symbol}")
            
            # 심볼 변경 성공 메시지 전송
            await self.send_personal_message(
                {
                    "type": "symbol_change",
                    "status": "success",
                    "old_symbol": old_symbol,
                    "new_symbol": new_symbol,
                    "message": "심볼이 성공적으로 변경되었습니다."
                },
                websocket
            )
            
        except Exception as e:
            logger.error(f"심볼 변경 중 오류 발생: {e}")
            raise