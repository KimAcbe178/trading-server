from pydantic import BaseModel
from typing import Dict, Any

class TradingSettings(BaseModel):
    default_leverage: int = 10
    default_quantity: float = 0.01
    risk_limit: float = 0.1
    max_positions: int = 5
    allowed_symbols: list[str] = ["BTCUSDT", "ETHUSDT"]

class APISettings(BaseModel):
    testnet: bool = True
    recv_window: int = 5000
    position_mode: bool = False  # False: One-way Mode, True: Hedge Mode

class Settings(BaseModel):
    trading: TradingSettings = TradingSettings()
    api: APISettings = APISettings()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        return cls(
            trading=TradingSettings(**data.get('trading', {})),
            api=APISettings(**data.get('api', {}))
        )