import pytest
import psutil
import os
import gc
from models.trading import OrderRequest
from decimal import Decimal

@pytest.mark.performance
class TestMemoryUsage:
    def get_memory_usage(self) -> float:
        """현재 프로세스의 메모리 사용량 조회 (MB)"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    @pytest.mark.asyncio
    async def test_memory_leak(self, trading_service):
        """메모리 누수 테스트"""
        initial_memory = self.get_memory_usage()
        
        # 반복적인 작업 수행
        for _ in range(100):
            order = await trading_service.place_order(
                OrderRequest(
                    symbol="BTCUSDT",
                    side="BUY",
                    quantity=Decimal("0.001"),
                    leverage=10
                )
            )
            await trading_service.close_position("BTCUSDT")
            
        # 가비지 컬렉션 강제 실행
        gc.collect()
        
        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가가 10MB 이하인지 확인
        assert memory_increase < 10