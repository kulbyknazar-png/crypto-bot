import requests
import ccxt
import pandas as pd
import mplfinance as mpf

# ======================
# TELEGRAM
# ======================
TOKEN = "8834703546:AAHy2MZwD2BaA2j-apTaSKC1qMl6kg8-UgY"
CHAT_ID = "8108131641"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ======================
# BINGX
# ======================
bingx = ccxt.bingx({"enableRateLimit": True})
symbol_bingx = "BTC/USDT"

# ======================
# MEXC SAFE DATA (FIXED 8 COLUMNS ISSUE)
# ======================
def get_mexc_ohlcv(symbol="BTCUSDT", interval="60m", limit=100):
    try:
        url = "https://api.mexc.com/api/v3/klines"

        r = requests.get(url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }, timeout=10)

        data = r.json()

        if not isinstance(data, list) or len(data) < 50:
            return None

        cleaned = []
        for c in data:
            cleaned.append([
                c[0], c[1], c[2], c[3], c[4], c[5]
            ])

        df = pd.DataFrame(cleaned, columns=[
            "time","open","high","low","close","volume"
        ])

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        df[["open","high","low","close","volume"]] = df[
            ["open","high","low","close","volume"]
        ].astype(float)

        df.set_index("time", inplace=True)

        return df

    except Exception as e:
        print("MEXC ERROR:", e)
        return None


# ======================
# BINGX DATA
# ======================
def get_bingx_ohlcv(tf="1h"):
    try:
        data = bingx.fetch_ohlcv(symbol_bingx, timeframe=tf, limit=100)

        if not data or len(data) < 50:
            return None

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume"
        ])

        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df.set_index("time", inplace=True)

        return df

    except Exception as e:
        print("BINGX ERROR:", e)
        return None


# ======================
# LEVELS
# ======================
def resistance(df):
    if df is None or len(df) < 50:
        return None
    return df["high"].rolling(50).max().iloc[-1]


def volume_ok(df):
    if df is None or len(df) < 20:
        return False
    return df["volume"].iloc[-1] > df["volume"].rolling(20).mean().iloc[-1]


# ======================
# CHART
# ======================
def make_chart(df, level):
    try:
        add_plot = mpf.make_addplot([level] * len(df), color="red")

        mpf.plot(
            df,
            type="candle",
            style="charles",
            addplot=add_plot,
            volume=True,
            savefig="chart.png"
        )
    except Exception as e:
        print("Chart error:", e)


# ======================
# MAIN
# ======================
def main():

    timeframes = {
        "1H": "1h",
        "2H": "2h",
        "4H": "4h"
    }

    # ======================
    # MEXC
    # ======================
    for tf_name, tf in timeframes.items():

        df = get_mexc_ohlcv("BTCUSDT", "60m")

        if df is None:
            print("MEXC NO DATA")
            continue

        level = resistance(df)
        if level is None:
            continue

        price = df["close"].iloc[-1]

        touch = abs(price - level) / level < 0.002
        vol = volume_ok(df)
        rejection = df["close"].iloc[-1] < df["open"].iloc[-1]

        print("MEXC:", tf_name, price, level, touch, vol, rejection)

        if touch and vol and rejection:

            make_chart(df, level)

            send_telegram(
                f"🔴 MEXC SIGNAL\n"
                f"TF: {tf_name}\n"
                f"Price: {price:.2f}\n"
                f"Level: {level:.2f}"
            )

    # ======================
    # BINGX
    # ======================
    for tf_name, tf in timeframes.items():

        df = get_bingx_ohlcv(tf)

        if df is None:
            print("BINGX NO DATA")
            continue

        level = resistance(df)
        if level is None:
            continue

        price = df["close"].iloc[-1]

        touch = abs(price - level) / level < 0.002
        vol = volume_ok(df)
        rejection = df["close"].iloc[-1] < df["open"].iloc[-1]

        print("BINGX:", tf_name, price, level, touch, vol, rejection)

        if touch and vol and rejection:

            make_chart(df, level)

            send_telegram(
                f"🔵 BINGX SIGNAL\n"
                f"TF: {tf_name}\n"
                f"Price: {price:.2f}\n"
                f"Level: {level:.2f}"
            )


# ======================
# RUN
# ======================
main()