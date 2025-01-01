import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from typing import List

@pytest.mark.performance
class TestAPIPerformance:
    @pytest.fixture(autouse=True)
    def setup(self, test_client: TestClient):
        self.client = test_client
        self.executor = ThreadPoolExecutor(max_workers=10)

    def make_request(self, endpoint: str) -> float:
        """단일 요청 실행 및 응답 시간 측정"""
        start_time = time.time()
        response = self.client.get(endpoint)
        assert response.status_code == 200
        return time.time() - start_time

    def test_price_api_performance(self):
        """가격 조회 API 성능 테스트"""
        endpoint = "/api/market/price/BTCUSDT"
        num_requests = 100
        
        # 동시 요청 실행
        response_times = list(
            self.executor.map(
                lambda _: self.make_request(endpoint),
                range(num_requests)
            )
        )
        
        # 성능 메트릭 계산
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # 성능 기준 검증
        assert avg_response_time < 0.1  # 평균 응답시간 100ms 이하
        assert max_response_time < 0.5  # 최대 응답시간 500ms 이하

    def test_positions_api_performance(self):
        """포지션 조회 API 성능 테스트"""
        endpoint = "/api/trading/positions"
        num_requests = 50
        
        response_times = list(
            self.executor.map(
                lambda _: self.make_request(endpoint),
                range(num_requests)
            )
        )
        
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.2  # 평균 응답시간 200ms 이하