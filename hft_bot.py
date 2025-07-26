hft_bot.py
# hft_bot.py
import asyncio
import aiohttp
import hmac
import hashlib
import time
import os
import json
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BASE_URL = "https://testnet.binance.vision"
WS_URL = "wss://testnet.binance.vision/ws/btcusdt@depth10@100ms"

symbol = "BTCUSDT"
spread = 1.5  # USD spread around mid-price
quantity = 0.001
paper_trading = True

session = None

async def place_order(side, price):
    if paper_trading:
        print(f"[PAPER] {side} order at {price:.2f}, quantity={quantity}")
        return {"status": "paper_trade", "side": side, "price": price, "quantity": quantity}

    endpoint = "/api/v3/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": quantity,
        "price": f"{price:.2f}",
        "recvWindow": 5000,
        "timestamp": timestamp
    }
    query_string = urlencode(params)
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature
    headers = {"X-MBX-APIKEY": API_KEY}

    async with session.post(BASE_URL + endpoint, params=params, headers=headers) as resp:
        data = await resp.json()
        print(f"Order Response: {data}")
        return data

async def handle_order_book():
    global session
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    bid = float(data['bids'][0][0])
                    ask = float(data['asks'][0][0])
                    mid_price = (bid + ask) / 2
                    buy_price = mid_price - spread / 2
                    sell_price = mid_price + spread / 2

                    print(f"Best Bid: {bid} | Best Ask: {ask} | Mid: {mid_price:.2f}")
                    await place_order("BUY", buy_price)
                    await place_order("SELL", sell_price)
                    await asyncio.sleep(1)
                else:
                    print(f"WebSocket Error: {msg}")

if __name__ == "__main__":
    asyncio.run(handle_order_book())
