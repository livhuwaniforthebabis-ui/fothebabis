import requests
import time

# ===== CONFIG =====
TELEGRAM_TOKEN = 8688692681:AAFeVYJxmVzrqWRpsr5ElhZL9yANv22iF84
CHAT_ID = -1003088214813
CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Add more coins if you want
INTERVAL = 300  # seconds between checks (5 minutes)import os
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

INTERVAL = 60
TIMEFRAME = "5m"

async def send_telegram(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    await session.post(url, data={"chat_id": CHAT_ID, "text": message})

def get_data(symbol):
    return yf.Ticker(symbol).history(period="1d", interval=TIMEFRAME).tail(50)

def detect_structure(data):
    highs = data['High']
    lows = data['Low']

    # Simple BOS logic
    if highs.iloc[-1] > highs.iloc[-10]:
        return "BULLISH"
    elif lows.iloc[-1] < lows.iloc[-10]:
        return "BEARISH"
    return None

def find_swing(data):
    # recent swing high/low
    swing_high = data['High'].rolling(5).max().iloc[-2]
    swing_low = data['Low'].rolling(5).min().iloc[-2]
    return swing_high, swing_low

def generate_trade(market, price, structure, swing_high, swing_low):
    if structure == "BULLISH":
        entry = price
        sl = swing_low
        risk = entry - sl

        tp1 = round(entry + risk, 2)        # 1R
        tp2 = round(entry + risk * 3, 2)    # 3R

        return {
            "direction": "BUY 📈",
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp1": tp1,
            "tp2": tp2,
            "rr": 3,
            "reason": "Bullish BOS + pullback into demand zone"
        }

    elif structure == "BEARISH":
        entry = price
        sl = swing_high
        risk = sl - entry

        tp1 = round(entry - risk, 2)
        tp2 = round(entry - risk * 3, 2)

        return {
            "direction": "SELL 📉",
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp1": tp1,
            "tp2": tp2,
            "rr": 3,
            "reason": "Bearish BOS + pullback into supply zone"
        }

    return None

async def main():
    print("🚀 SMC 1:3 RR Bot Running...")
    async with aiohttp.ClientSession() as session:
        while True:
            for market, symbol in MARKETS.items():
                try:
                    data = get_data(symbol)
                    price = data['Close'].iloc[-1]

                    structure = detect_structure(data)
                    if not structure:
                        continue

                    swing_high, swing_low = find_swing(data)

                    trade = generate_trade(market, price, structure, swing_high, swing_low)
                    if not trade:
                        continue

                    message = f"""
💹 {market}
⏱️ TF: {TIMEFRAME}

📊 Direction: {trade['direction']}
📍 Entry: {trade['entry']}

🛑 Stop Loss: {trade['sl']}
💰 Partial TP (1R): {trade['tp1']}
🎯 Final TP (3R): {trade['tp2']}

🔒 Move SL to BE at 1R
⚖️ Risk/Reward: 1:{trade['rr']}

🧠 SMC Analysis:
• Structure: {structure} BOS
• Setup: {trade['reason']}
• Entry Type: Pullback continuation

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
                    await send_telegram(session, message)

                except Exception as e:
                    print("Error:", e)

            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
PRICE_CHANGE_THRESHOLD = 0.01  # 1% change for BUY/SELL

# ===== FUNCTIONS =====
def get_price(symbol):
    """Fetch current price from Binance API"""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    return float(response['price'])

def generate_signal(current, previous):
    """Simple rule-based signal"""
    if previous is None:
        return "⚪ HOLD"
    change = (current - previous) / previous
    if change >= PRICE_CHANGE_THRESHOLD:
        return "📈 BUY"
    elif change <= -PRICE_CHANGE_THRESHOLD:
        return "📉 SELL"
    else:
        return "⚪ HOLD"

def send_telegram(message):
    """Send message to Telegram channel/group"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def format_message(symbol, price, signal, percent_change):
    """Format message with trend and percent change"""
    return (
        f"{symbol} Signal\n"
        f"Price: ${price:.2f}\n"
        f"Signal: {signal}\n"
        f"Change since last: {percent_change:+.2f}%"
    )

# ===== MAIN LOOP =====
previous_prices = {symbol: None for symbol in CRYPTO_SYMBOLS}
previous_signals = {symbol: None for symbol in CRYPTO_SYMBOLS}

while True:
    for symbol in CRYPTO_SYMBOLS:
        try:
            price = get_price(symbol)
            prev_price = previous_prices[symbol]
            signal = generate_signal(price, prev_price)
            
            # Calculate percent change
            percent_change = ((price - prev_price) / prev_price * 100) if prev_price else 0
            
            # Only send message if signal changed
            if signal != previous_signals[symbol]:
                message = format_message(symbol, price, signal, percent_change)
                send_telegram(message)
                print(f"✅ Sent {symbol} signal: {signal} ({percent_change:+.2f}%)")
                previous_signals[symbol] = signal
            
            previous_prices[symbol] = price
        except Exception as e:
            print(f"❌ Error with {symbol}: {e}")
    time.sleep(INTERVAL)
