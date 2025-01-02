from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Dict

class MetricsManager:
    def __init__(self):
        # 거래 관련 메트릭
        self.order_counter = Counter(
            'trading_orders_total',
            'Total number of orders',
            ['symbol', 'side', 'status']
        )

        self.position_gauge = Gauge(
            'trading_positions',
            'Current positions',
            ['symbol', 'side']
        )

        self.pnl_gauge = Gauge(
            'trading_pnl',
            'Current PnL',
            ['symbol']
        )

        # API 성능 메트릭
        self.api_latency = Histogram(
            'api_request_latency_seconds',
            'API request latency',
            ['endpoint']
        )

        # 바이낸스 API 메트릭
        self.binance_requests = Counter(
            'binance_api_requests_total',
            'Total Binance API requests',
            ['endpoint', 'status']
        )

        # 시스템 메트릭
        self.active_connections = Gauge(
            'websocket_active_connections',
            'Number of active WebSocket connections'
        )

        self.memory_usage = Gauge(
            'app_memory_usage_bytes',
            'Memory usage in bytes'
        )

    def setup_fastapi_metrics(self, app):
        """FastAPI 메트릭 설정"""
        Instrumentator().instrument(app).expose(app)

metrics = MetricsManager()