from typing import List, Optional
from fastapi import HTTPException
from binance.client import Client
from binance.exceptions import BinanceAPIException
from src.utils.logger import logger
from src.models.trading import OrderRequest
from src.config.env import EnvConfig

class BinanceService:
    def __init__(self):
        self.client = None
        self.testnet = EnvConfig.USE_TESTNET
        self.api_key = EnvConfig.BINANCE_API_KEY
        self.api_secret = EnvConfig.BINANCE_API_SECRET

    async def initialize(self):
        """바이낸스 클라이언트 초기화"""
        try:
            self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
            # 선물 계정 접근 권한 확인
            account = self.client.futures_account()
            logger.info(f"선물 계정 접근 권한 확인 완료")
            logger.info(f"계정 정보: {account['totalWalletBalance']} USDT")
            logger.info("바이낸스 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"바이낸스 클라이언트 초기화 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cleanup(self):
        """바이낸스 클라이언트 정리"""
        try:
            if self.client:
                self.client.close_connection()
            logger.info("바이낸스 클라이언트 연결 종료")
        except Exception as e:
            logger.error(f"바이낸스 클라이언트 정리 실패: {e}")

    async def get_all_positions(self) -> List[dict]:
        """현재 포지션 조회"""
        try:
            positions = self.client.futures_position_information()
            leverage_info = self.client.futures_leverage_bracket()  # 레버리지 정보 조회
            
            # 레버리지 정보를 심볼별로 매핑
            leverage_map = {item['symbol']: item['leverage'] for item in leverage_info}
            
            active_positions = []
            for pos in positions:
                if float(pos["positionAmt"]) != 0:
                    try:
                        notional = abs(float(pos.get("notional", 0)))
                        isolated_margin = float(pos.get("isolatedMargin", 0))
                        
                        position_info = {
                            "symbol": pos["symbol"],
                            "positionAmt": float(pos["positionAmt"]),
                            "entryPrice": float(pos["entryPrice"]),
                            "markPrice": float(pos["markPrice"]),
                            "unrealizedProfit": float(pos["unRealizedProfit"]),
                            "liquidationPrice": float(pos.get("liquidationPrice", 0)),
                            "notional": notional,
                            "isolatedMargin": isolated_margin,
                            "marginAsset": pos.get("marginAsset", "USDT"),
                            "leverage": leverage_map.get(pos["symbol"], 10),  # 기본값 10
                            "positionSide": pos.get("positionSide", "BOTH")
                        }
                        
                        active_positions.append(position_info)
                    except (KeyError, ValueError) as e:
                        logger.error(f"포지션 데이터 처리 실패: {e}, 데이터: {pos}")
                        continue
            
            return active_positions
        except BinanceAPIException as e:
            logger.error(f"바이낸스 API 오류: {e}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
            return active_positions
        except BinanceAPIException as e:
            logger.error(f"바이낸스 API 오류: {e}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"포지션 조회 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_order(self, order: OrderRequest) -> dict:
        """주문 생성"""
        try:
            # 주문 파라미터 설정
            params = {
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "quantity": order.quantity
            }

            # 지정가 주문인 경우 가격 추가
            if order.type == "LIMIT":
                if not order.price:
                    raise HTTPException(status_code=400, detail="Limit order requires price")
                params["price"] = order.price
                params["timeInForce"] = "GTC"

            # 주문 실행
            response = self.client.futures_create_order(**params)
            logger.info(f"주문 생성 완료: {response}")
            return response

        except BinanceAPIException as e:
            logger.error(f"바이낸스 API 오류: {e}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"주문 생성 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_account_info(self) -> dict:
        """계정 정보 조회"""
        try:
            account = self.client.futures_account()
            return {
                "totalWalletBalance": float(account["totalWalletBalance"]),
                "totalUnrealizedProfit": float(account["totalUnrealizedProfit"]),
                "totalMarginBalance": float(account["totalMarginBalance"]),
                "availableBalance": float(account["availableBalance"]),
                "maxWithdrawAmount": float(account["maxWithdrawAmount"])
            }
        except BinanceAPIException as e:
            logger.error(f"바이낸스 API 오류: {e}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"계정 정보 조회 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_exchange_info(self) -> dict:
        """거래소 정보 조회"""
        try:
            exchange_info = self.client.futures_exchange_info()
            return exchange_info
        except BinanceAPIException as e:
            logger.error(f"바이낸스 API 오류: {e}")
            raise HTTPException(status_code=e.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"거래소 정보 조회 실패: {e}")
            raise HTTPException(status_code=500, detail=str(e))