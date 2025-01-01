from fastapi.testclient import TestClient
from decimal import Decimal

def test_get_settings(test_client: TestClient):
    """설정 조회 API 테스트"""
    response = test_client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "trading" in data
    assert "api" in data

def test_get_mark_price(test_client: TestClient):
    """마크 가격 조회 API 테스트"""
    response = test_client.get("/api/market/price/BTCUSDT")
    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data
    assert "price" in data
    assert data["symbol"] == "BTCUSDT"
    assert float(data["price"]) > 0

def test_place_order(test_client: TestClient):
    """주문 실행 API 테스트"""
    order_data = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": "0.001",
        "leverage": 10
    }
    
    response = test_client.post("/api/trading/order", json=order_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["side"] == "BUY"

def test_get_positions(test_client: TestClient):
    """포지션 조회 API 테스트"""
    response = test_client.get("/api/trading/positions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)