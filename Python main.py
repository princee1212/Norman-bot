import requests
import time
import os
from collections import defaultdict

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

# Track token activity
token_tracker = defaultdict(list)

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== GET SWAPS =====
def get_swaps():
    url = f"https://deep-index.moralis.io/api/v2/{PANCAKE_ROUTER}/erc20/transfers?chain=bsc"

    headers = {
        "accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if "result" not in data:
        return

    for tx in data["result"][:30]:
        try:
            usd_value = float(tx.get("value_usd", 0))
            if usd_value < 10000:
                continue

            token_name = tx.get("token_name", "Unknown")
            token_symbol = tx.get("token_symbol", "")
            contract = tx.get("address")

            if token_symbol in ["USDT", "USDC", "BUSD"]:
                continue

            buyer = tx.get("to_address")

            # Track buys
            token_tracker[contract].append(buyer)

            # Remove duplicates (same wallet)
            unique_buyers = list(set(token_tracker[contract]))

            count = len(unique_buyers)

            # ===== SIGNAL LOGIC =====
            if count >= 3:
                signal = "🔥 MULTI-WHALE ACCUMULATION"
            elif count == 2:
                signal = "⚠️ BUILDING MOMENTUM"
            else:
                signal = "🟡 SINGLE WHALE"

            # Only alert when meaningful
            if count >= 2:
                message = f"""
🚨 NORMAN V3 SIGNAL

Token: {token_name} ({token_symbol})
Buy Size: ${usd_value:,.2f}
Contract: {contract}

Whale Buyers: {count}
Signal: {signal}

Chain: BNB (PancakeSwap)
"""
                send_telegram(message)

        except:
            continue

# ===== LOOP =====
while True:
    get_swaps()
    send_telegram("Heartbeat: Norman running ✅")
    time.sleep(60)
