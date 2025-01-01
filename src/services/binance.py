from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
from dotenv import load_dotenv

load_dotenv()

class BinanceService:
    def __init__(self):
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_SECRET_KEY')
        )
    
    def create_order(self, symbol: str, side: str, quantity: float):
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            return order
        except BinanceAPIException as e:
            print(f'Error creating order: {e}')
            raise e
