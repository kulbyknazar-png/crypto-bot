import ccxt
from telegram import Bot
import asyncio

TOKEN = "8834703546:AAHy2MZwD2BaA2j-apTaSKC1qMl6kg8-UgY"
CHAT_ID = "8108131641"

mexc = ccxt.mexc()
bingx = ccxt.bingx()

symbol = "BTC/USDT"

def get_resistance(exchange):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
    highs = [candle[2] for candle in ohlcv]
    return max(highs)

async def send_signal(text):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():

    mexc_res = get_resistance(mexc)
    bingx_res = get_resistance(bingx)

    mexc_price = mexc.fetch_ticker(symbol)["last"]
    bingx_price = bingx.fetch_ticker(symbol)["last"]

    # проверка касания уровня
    if abs(mexc_price - mexc_res) / mexc_res < 0.002:
        await send_signal(
            f"🔴 MEXC REJECTION\n\n"
            f"Resistance: {mexc_res:.2f}\n"
            f"Price: {mexc_price:.2f}\n"
            f"Signal: Possible rejection 📉"
        )

    if abs(bingx_price - bingx_res) / bingx_res < 0.002:
        await send_signal(
            f"🔴 BINGX REJECTION\n\n"
            f"Resistance: {bingx_res:.2f}\n"
            f"Price: {bingx_price:.2f}\n"
            f"Signal: Possible rejection 📉"
        )

asyncio.run(main())