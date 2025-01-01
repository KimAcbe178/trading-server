from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime

OrderSide = Literal['BUY', 'SELL']
PositionSide = Literal['LONG', 'SHORT']
OrderStatus = Literal['NEW', 'FILLED', 'CANCELED', 'REJECTED']

class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: Decimal
    leverage: int = Field(ge=1, le=125)
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

class Order(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    leverage: int
    status: OrderStatus
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_binance(cls, data: dict) -> 'Order':
        return cls(
            id=data['orderId'],
            symbol=data['symbol'],
            side=data['side'],
            quantity=Decimal(str(data['origQty'])),
            price=Decimal(str(data['avgPrice'])) if data['avgPrice'] != '0' else Decimal(str(data['price'])),
            leverage=int(data['leverage']),
            status=data['status'],
            created_at=datetime.fromtimestamp(data['time'] / 1000)
        )

class Position(BaseModel):
    symbol: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    leverage: int
    margin: Decimal
    liquidation_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = Decimal('0')
    
    @classmethod
    def from_binance(cls, data: dict) -> 'Position':
        quantity = Decimal(str(data['positionAmt']))
        return cls(
            symbol=data['symbol'],
            side='LONG' if quantity > 0 else 'SHORT',
            quantity=abs(quantity),
            entry_price=Decimal(str(data['entryPrice'])),
            leverage=int(data['leverage']),
            margin=Decimal(str(data['isolatedMargin'])),
            liquidation_price=Decimal(str(data['liquidationPrice'])) if data['liquidationPrice'] != '0' else None,
            unrealized_pnl=Decimal(str(data['unrealizedProfit']))
        )