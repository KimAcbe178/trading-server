from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class TradingSignal(BaseModel):
    action: str  # LONG, SHORT, EXIT
    symbol: str
    price: float

@app.get('/')
async def root():
    return {'status': 'running'}

@app.post('/webhook')
async def webhook(signal: TradingSignal):
    try:
        print(f'Received signal: {signal}')
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
