from fastapi import WebSocket
from typing import Dict, Set
from utils.logger import logger

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        """WebSocket 연결 추가"""
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = set()
        self.active_connections[symbol].add(websocket)
        logger.info(f"새로운 WebSocket 연결: {symbol}")

    def disconnect(self, websocket: WebSocket, symbol: str):
        """WebSocket 연결 제거"""
        if symbol in self.active_connections:
            self.active_connections[symbol].discard(websocket)
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]
            logger.info(f"WebSocket 연결 종료: {symbol}")

    async def broadcast(self, symbol: str, message: dict):
        """특정 심볼의 모든 연결에 메시지 브로드캐스트"""
        if symbol in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[symbol]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"메시지 전송 실패: {e}")
                    disconnected.add(connection)
            
            # 끊어진 연결 제거
            for connection in disconnected:
                self.disconnect(connection, symbol)

    def get_subscribers(self, symbol: str) -> Set[WebSocket]:
        """특정 심볼의 구독자 목록 반환"""
        return self.active_connections.get(symbol, set())

    def get_active_symbols(self) -> Set[str]:
        """활성화된 심볼 목록 반환"""
        return set(self.active_connections.keys())

    async def close_all(self):
        """모든 연결 종료"""
        for symbol in list(self.active_connections.keys()):
            for connection in list(self.active_connections[symbol]):
                await connection.close()
            self.active_connections[symbol].clear()
        self.active_connections.clear()
        logger.info("모든 WebSocket 연결 종료")