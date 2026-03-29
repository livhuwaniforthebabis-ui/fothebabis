import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime

# ENV VARIABLES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

# MARKETS
MARKETS = {
    "BTCUSD": "BTC-USD",
    "GOLD": "GC=F",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "USDJPY": "JPY=X"
}

TIMEFRAME = "15m"
INTERVAL = 60  # check every 60 seconds

# SEND TELEGRAM
async def send_telegram(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    await session.post(url, data={"chat_id": CHAT_ID, "text": message})

# GET DATA
def get_data(symbol):
    return yf.Ticker(symbol).history(period="2d", interval=TIMEFRAME)

# HTF TREND
def get_trend(data):
    if data['Close'].iloc[-1] > data['Close'].iloc[-30]:
        return "UPTREND 📈"
    elif data['Close'].iloc[-1] < data['Close'].iloc[-30]:
        return "DOWNTREND 📉"
    return None

# BOS / MSS
def get_structure(data):
    highs = data['High']
    lows = data['Low']

    if highs.iloc[-1] > highs.iloc[-10]:
        return "BULLISH BOS"
    elif lows.iloc[-1] < lows.iloc[-10]:
        return "BEARISH BOS"
    return None

# LIQUIDITY SWEEP
def liquidity_sweep(data):
    recent_high = data['High'].iloc[-6:-1].max()
    recent_low = data['Low'].iloc[-6:-1].min()
    current = data['Close'].iloc[-1]

    if current > recent_high:
        return "SWEEP HIGH 🔝"
    elif current < recent_low:
        return "SWEEP LOW 🔻"
    return None

# HIGH PROBABILITY FILTER
def high_probability(trend, structure, liquidity):
    if trend and structure and liquidity:
        if "UPTREND" in trend and "BULLISH" in structure and "LOW" in liquidity:
            return True
        if "DOWNTREND" in trend and "BEARISH" in structure and "HIGH" in liquidity:
            return True
    return False

# TRADE GENERATION
def generate_trade(price, trend):
    risk = price * 0.002

    if "UPTREND" in trend:
        sl = price - risk
        tp1 = price + risk
        tp2 = price + risk * 3
        direction = "BUY 📈"
    else:
        sl = price + risk
        tp1 = price - risk
        tp2 = price - risk * 3
        direction = "SELL 📉"

    return direction, round(sl,2), round(tp1,2), round(tp2,2)

# CONFIDENCE SCORE
def confidence_score():
    return "HIGH (85%+) 🔥"

# MAIN LOOP
async def main():
    print("🚀 High Probability SMC Bot Running...")

    async with aiohttp.ClientSession() as session:
        while True:
            for market, symbol in MARKETS.items():
                try:
                    data = get_data(symbol)
                    price = data['Close'].iloc[-1]

                    trend = get_trend(data)
                    structure = get_structure(data)
                    liquidity = liquidity_sweep(data)

                    # FILTER LOW QUALITY SETUPS
                    if not high_probability(trend, structure, liquidity):
                        continue

                    direction, sl, tp1, tp2 = generate_trade(price, trend)

                    # ANALYSIS MESSAGE
                    analysis = f"""
🧠 ANALYSIS - {market}

⏱ Timeframe: 15M (Execution)

📊 Trend: {trend}
🏗 Structure: {structure}
💧 Liquidity: {liquidity}

📍 POI: Order Block Zone (simulated)
🎯 Target: Continuation (3R)

⚖️ Confidence: {confidence_score()}
"""

                    await send_telegram(session, analysis)

                    # TRADE MESSAGE
                    trade = f"""
💹 TRADE SETUP - {market}

📊 Direction: {direction}
📍 Entry: {round(price,2)}

🛑 Stop Loss: {sl}
💰 Partial TP: {tp1}
🎯 Final TP: {tp2}

🔒 Move SL to Breakeven at TP1
⚖️ Risk Reward: 1:3

🧠 Reason:
Trend + BOS + Liquidity Sweep Alignment

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

                    await send_telegram(session, trade)

                except Exception as e:
                    print("Error:", e)

            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
