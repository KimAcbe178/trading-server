import pytest
import asyncio
import aiohttp
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestLoadPerformance:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.base_url = "http://localhost:8000"
        self.session = aiohttp.ClientSession()
        yield
        await self.session.close()

    async def make_request(self, endpoint: str) -> float:
        """비동기 요청 실행"""
        start_time = time.time()
        async with self.session.get(f"{self.base_url}{endpoint}") as response:
            assert response.status == 200
            await response.json()
        return time.time() - start_time

    async def run_concurrent_requests(
        self, 
        endpoint: str, 
        num_requests: int
    ) -> List[float]:
        """동시 요청 실행"""
        tasks = [
            self.make_request(endpoint) 
            for _ in range(num_requests)
        ]
        return await asyncio.gather(*tasks)

    @pytest.mark.asyncio
    async def test_high_load_price_api(self):
        """가격 API 부하 테스트"""
        endpoint = "/api/market/price/BTCUSDT"
        num_requests = 1000
        
        response_times = await self.run_concurrent_requests(
            endpoint, 
            num_requests
        )
        
        # 성능 메트릭 계산
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        requests_per_second = num_requests / sum(response_times)
        
        # 성능 기준 검증
        assert avg_response_time < 0.1
        assert max_response_time < 1.0
        assert requests_per_second > 100

    @pytest.mark.asyncio
    async def test_websocket_performance(self):
        """WebSocket 성능 테스트"""
        uri = f"{self.base_url}/ws"
        message_count = 0
        start_time = time.time()
        
        async with self.session.ws_connect(uri) as ws:
            # 구독 메시지 전송
            await ws.send_json({
                "type": "subscribe",
                "symbol": "BTCUSDT"
            })
            
            # 1초 동안 메시지 수신
            while time.time() - start_time < 1:
                msg = await ws.receive_json()
                if msg["type"] == "price":
                    message_count += 1
        
        # 초당 최소 10개의 메시지 수신 확인
        assert message_count >= 10