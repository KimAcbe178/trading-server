from fastapi import HTTPException

class TradingException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class BinanceError(TradingException):
    def __init__(self, detail: str):
        super().__init__(detail=f"Binance API Error: {detail}")

class ValidationError(TradingException):
    def __init__(self, detail: str):
        super().__init__(detail=f"Validation Error: {detail}")

class PositionError(TradingException):
    def __init__(self, detail: str):
        super().__init__(detail=f"Position Error: {detail}")

class OrderError(TradingException):
    def __init__(self, detail: str):
        super().__init__(detail=f"Order Error: {detail}")