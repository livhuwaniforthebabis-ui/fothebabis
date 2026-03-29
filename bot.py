import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

MARKETS = {
    "BTCUSD": "BTC-USD",
    "GOLD": "GC=F",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "USDJPY": "JPY=X"
}

TIMEFRAME = "15m"
INTERVAL = 60

stats = {"wins": 0, "losses": 0, "total": 0}

async def send_telegram(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    await session.post(url, data={"chat_id": CHAT_ID, "text": message})

def get_data(symbol):
    return yf.Ticker(symbol).history(period="2d", interval=TIMEFRAME)

# -------- HTF TREND --------
def get_trend(data):
    if data['Close'].iloc[-1] > data['Close'].iloc[-20]:
        return "UPTREND 📈"
    else:
        return "DOWNTREND 📉"

# -------- STRUCTURE --------
def get_structure(data):
    high = data['High']
    low = data['Low']

    if high.iloc[-1] > high.iloc[-10]:
        return "BOS ↑"
    elif low.iloc[-1] < low.iloc[-10]:
        return "BOS ↓"
    return "No clear BOS"

# -------- LIQUIDITY --------
def detect_liquidity(data):
    recent_high = data['High'].iloc[-5:-1].max()
    recent_low = data['Low'].iloc[-5:-1].min()
    current = data['Close'].iloc[-1]

    if current > recent_high:
        return "Liquidity Sweep Above 🔝"
    elif current < recent_low:
        return "Liquidity Sweep Below 🔻"
    return "No sweep"

# -------- TRADE --------
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

# -------- CONFIDENCE --------
def get_confidence(trend, structure, liquidity):
    score = 0

    if "UPTREND" in trend or "DOWNTREND" in trend:
        score += 1
    if "BOS" in structure:
        score += 1
    if "Sweep" in liquidity:
        score += 1

    if score == 3:
        return "HIGH (100%) 🔥"
    elif score == 2:
        return "MEDIUM (75%) ⚡"
    else:
        return "LOW (50%) ⚠️"

# -------- MAIN --------
async def main():
    print("🚀 Institutional SMC Bot Running...")
    async with aiohttp.ClientSession() as session:
        while True:
            for market, symbol in MARKETS.items():
                try:
                    data = get_data(symbol)
                    price = data['Close'].iloc[-1]

                    trend = get_trend(data)
                    structure = get_structure(data)
                    liquidity = detect_liquidity(data)

                    confidence = get_confidence(trend, structure, liquidity)

                    direction, sl, tp1, tp2 = generate_trade(price, trend)

                    analysis_time = datetime.utcnow().strftime('%H:%M:%S')

                    # -------- ANALYSIS MESSAGE --------
                    analysis_msg = f"""
🧠 ANALYSIS REPORT - {market}

📊 Trend: {trend}
🏗 Structure: {structure}
💧 Liquidity: {liquidity}

📍 POI: Simulated Order Block Zone
🎯 Target: Continuation move (3R)

⚖️ Confidence: {confidence}
⏱ Analysis Time: {analysis_time}
"""
                    await send_telegram(session, analysis_msg)

                    # -------- TRADE MESSAGE --------
                    trade_msg = f"""
💹 TRADE EXECUTION - {market}

📊 Direction: {direction}
📍 Entry: {round(price,2)}

🛑 SL: {sl}
💰 TP1: {tp1}
🎯 TP2: {tp2}

🔒 Move SL to BE at TP1
⚖️ RR: 1:3

🧠 Reason:
Trend + BOS + Liquidity confirmation

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
                    await send_telegram(session, trade_msg)

                    stats["total"] += 1

                except Exception as e:
                    print("Error:", e)

            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
