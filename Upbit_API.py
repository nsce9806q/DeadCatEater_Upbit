import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import websockets
import asyncio
import json

import requests

from time import sleep, strftime, localtime, time

class Upbit_API:
    server_url = 'https://api.upbit.com'
    KRW_balance = '0' # KRW 잔액
    volume = '0' # 코인 수량
    avg_price = '0' # 평균 단가
    coin = '\0' # 코인
    order_uuid = '\0' # 주문 번호
    profit_price = '0' # 기대 이익 단가
    loss_price = '0' # 손절 단가
    order_state = '\0' # 주문 상태 wait: 체결 대기 / watch: 예약주문 대기 / done: 체결 완료 / cancel: 주문 취소

    # 생성자
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key

    # 소멸자
    def __del__(self):
        print('소멸')

    # 코인 설정
    def select_market(self, value):
        self.coin = value

    # 이익 기댓값 설정
    def profit_expect(self, value):
        self.profit_price = str(self.round_unit(float(self.avg_price) * (1+value)))

    # 손절 라인 설정
    def stoploss(self, value):
        self.loss_price = str(self.round_unit(float(self.avg_price) * (1-value)))
    
    # 시장가 매수
    def buy_market(self):
        query = {
            'market': 'KRW-{}'.format(self.coin),
            'side': 'bid',
            'price': str(float(self.KRW_balance)-2000), 
            'ord_type': 'price'
        }

        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.post(self.server_url + "/v1/orders", params=query, headers=headers)

        print('시장가 매수 주문')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())

    # 지정가 매도
    def sell_limit(self):
        query = {
            'market': 'KRW-{}'.format(self.coin),
            'side': 'ask',
            'volume': self.volume,
            'price': self.profit_price,
            'ord_type': 'limit'
        }

        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.post(self.server_url + "/v1/orders", params=query, headers=headers)

        data = res.json()
        self.order_uuid = data['uuid']

        print('지정가 매도 주문')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())

    # 시장가 매도 (손절)
    def sell_market(self):
        query = {
            'market': 'KRW-{}'.format(self.coin),
            'side': 'ask',
            'volume': self.volume,
            'ord_type': 'market'
        }

        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.post(self.server_url + "/v1/orders", params=query, headers=headers)

        print('손절')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())

    # 주문 취소
    def order_cancel(self):
        query = {
            'uuid': self.order_uuid,
        }
        
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.delete(self.server_url + "/v1/order", params=query, headers=headers)

        print('주문 취소')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())

    # 주문 조회
    def order_inquiry(self):
        query = {
            'uuid': self.order_uuid,
        }
        
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
            }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(self.server_url + "/v1/order", params=query, headers=headers)

        data = res.json()
        self.order_state = data['state']

        print('주문 조회')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())

    # KRW 잔액 조회
    def check_KRW(self):

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(self.server_url + "/v1/accounts", headers=headers)

        data = res.json()

        self.KRW_balance = data[0]['balance']

        print('KRW 조회')
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())    

        # res.json() 예시
        # [{'currency': 'KRW', 'balance': '726418.14648042', 'locked': '0.0', 'avg_buy_price': '0', 'avg_buy_price_modified': True, 'uni': '0', 'avg_buy_price_modified': True, 'unit_currency': 'KRW'}]

    # 코인 잔액 조회
    def check_coin(self):

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(self.server_url + "/v1/accounts", headers=headers)

        data = res.json()

        for i in range(len(data)):
            if (data[i]['currency'] == self.coin):
                self.volume = data[i]['balance']
                self.avg_price = data[i]['avg_buy_price']

        print('{} 조회'.format(self.coin))
        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
        print(res.json())    

    async def upbit_ws_client(self):
        uri = "wss://api.upbit.com/websocket/v1"

        async with websockets.connect(uri) as websocket:
            subscribe_fmt = [
                {"ticket":"test"},
                {
                    "type":"ticker",
                    "codes":["KRW-{}".format(self.coin)], # 마켓 선택
                    "isOnlyRealtime":True
                },
                {"format":"SIMPLE"}
            ]
            subscribe_data = json.dumps(subscribe_fmt)
            await websocket.send(subscribe_data)

            print("가격 조회중")
            while True:
                data = await websocket.recv()
                data = json.loads(data)
            
                # 손절 라인 가격이 되면 지정가 매도 취소 후 시장가 매도하고 break
                if (float(self.loss_price) <= data.get('tp')):
                    self.order_cancel()
                    self.sell_market()
                    print('손절')
                    print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
                    break
                # 이익 기댓값 이상일 경우 주문 상태 확인 후 break
                elif (self.profit_price >= data.get('tp')):
                    self.order_inquiry()
                    if(self.order_state == 'done'):
                        print('GAY득')
                        print(strftime('%y-%m-%d %H:%M:%S', localtime(time())))
                        break
                    
    async def main(self):
        await self.upbit_ws_client()

    def websocket_start(self):
        asyncio.run(self.main())

    # KRW 마켓 주문 단위
    def round_unit(self, value):
        if (value < 10):
            rounded_price = round(value, 2)
        elif (value < 100):
            rounded_price = round(value, 1)
        elif (value < 1000):
            rounded_price = round(value)
        elif (value < 10000):
            rounded_price = round(value) - round(value)%5
        elif (value < 100000):
            rounded_price = round(value) - round(value)%10
        elif (value < 500000):
            rounded_price = round(value) - round(value)%50
        elif (value < 1000000):
            rounded_price = round(value) - round(value)%100
        elif (value < 2000000):
            rounded_price = round(value) - round(value)%500
        else:
            rounded_price = round(value) - round(value)%1000
    
        return rounded_price