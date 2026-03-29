import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

MARKETS = {
    "BTCUSD": "BTC-USD",
    "GOLD": "GC=F",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "USDJPY": "JPY=X"
}

TIMEFRAME = "5m"
INTERVAL = 60  # seconds

# Prevent duplicate signals
last_signal = {m: None for m in MARKETS}

# ================= TELEGRAM =================
async def send_telegram(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        async with session.post(url, data={"chat_id": CHAT_ID, "text": message}) as resp:
            await resp.text()
    except Exception as e:
        print("Telegram error:", e)

# ================= DATA =================
def get_data(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d", interval=TIMEFRAME)
        return data.tail(50)
    except:
        return None

# ================= SMC LOGIC =================
def detect_structure(data):
    highs = data['High']
    lows = data['Low']

    if highs.iloc[-1] > highs.iloc[-10]:
        return "BULLISH"
    elif lows.iloc[-1] < lows.iloc[-10]:
        return "BEARISH"
    return None

def find_swings(data):
    swing_high = data['High'].rolling(5).max().iloc[-2]
    swing_low = data['Low'].rolling(5).min().iloc[-2]
    return swing_high, swing_low

def generate_trade(price, structure, swing_high, swing_low):
    if structure == "BULLISH":
        sl = swing_low
        risk = price - sl

        if risk <= 0:
            return None

        tp1 = price + risk       # 1R
        tp2 = price + (risk * 3) # 3R

        return {
            "type": "BUY",
            "entry": round(price, 2),
            "sl": round(sl, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "rr": "1:3",
            "reason": "Bullish BOS + pullback continuation"
        }

    elif structure == "BEARISH":
        sl = swing_high
        risk = sl - price

        if risk <= 0:
            return None

        tp1 = price - risk
        tp2 = price - (risk * 3)

        return {
            "type": "SELL",
            "entry": round(price, 2),
            "sl": round(sl, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "rr": "1:3",
            "reason": "Bearish BOS + pullback continuation"
        }

    return None

# ================= MAIN LOOP =================
async def main():
    print("🚀 SMC Bot Running...")

    async with aiohttp.ClientSession() as session:
        while True:
            for market, symbol in MARKETS.items():
                try:
                    data = get_data(symbol)
                    if data is None or data.empty:
                        continue

                    price = data['Close'].iloc[-1]

                    structure = detect_structure(data)
                    if not structure:
                        continue

                    swing_high, swing_low = find_swings(data)

                    trade = generate_trade(price, structure, swing_high, swing_low)
                    if not trade:
                        continue

                    signal_id = f"{market}_{trade['type']}_{trade['entry']}"

                    # Prevent duplicate signals
                    if last_signal[market] == signal_id:
                        continue

                    message = f"""
💹 {market}
⏱️ Timeframe: {TIMEFRAME}

📊 Direction: {trade['type']} {"📈" if trade['type']=="BUY" else "📉"}
📍 Entry: {trade['entry']}

🛑 Stop Loss: {trade['sl']}
💰 Partial TP (1R): {trade['tp1']}
🎯 Final TP (3R): {trade['tp2']}

🔒 Move SL to Breakeven at TP1
⚖️ Risk/Reward: {trade['rr']}

🧠 Analysis:
• Structure: {structure} BOS
• Setup: {trade['reason']}
• Model: SMC Pullback Strategy

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

                    await send_telegram(session, message)
                    last_signal[market] = signal_id

                    print(f"Sent {market} {trade['type']}")

                except Exception as e:
                    print(f"Error {market}:", e)

            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
