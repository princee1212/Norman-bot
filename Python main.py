import requests
import time
import os

BOT_TOKEN = os.getenv("8793259832:AAHUmarr6U7JL4elvtdffb0kjr9ZAok-860")
CHAT_ID = os.getenv("8432602325")
MORALIS_API_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjdiNmIyZmY3LTg4ZDAtNDM0YS05NjcyLWZkYTExMmQ3NmE0OSIsIm9yZ0lkIjoiNTA5NzEwIiwidXNlcklkIjoiNTI0NDMxIiwidHlwZUlkIjoiMjllMGY5NWYtYzhlMC00ZTUwLWFlMTctYjI4NDk4NTY1M2E4IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzYyMDg2MTcsImV4cCI6NDkzMTk2ODYxN30.hw6XPrgXmnzj5GRkb6AUDplYHWg5phCDHZTRp7qcOvs")

# PancakeSwap Router (BNB Chain)
PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

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

    for tx in data["result"][:20]:
        try:
            usd_value = float(tx.get("value_usd", 0))

            if usd_value < 10000:
                continue

            token_name = tx.get("token_name", "Unknown")
            token_symbol = tx.get("token_symbol", "")
            contract = tx.get("address")

            # ===== SIMPLE FILTERS =====
            if token_name is None or len(token_name) < 2:
                continue

            # Ignore stablecoins (basic filter)
            if token_symbol in ["USDT", "USDC", "BUSD"]:
                continue

            # ===== SIGNAL LOGIC =====
            signal = "⚠️ WATCH"

            if usd_value > 50000:
                signal = "🔥 STRONG BUY"

            if usd_value > 100000:
                signal = "🚀 WHALE ACCUMULATION"

            message = f"""
🚨 NORMAN SIGNAL V2

Token: {token_name} ({token_symbol})
Buy Size: ${usd_value:,.2f}
Contract: {contract}

DEX: PancakeSwap (BNB)
Signal: {signal}
"""

            send_telegram(message)

        except:
            continue

# ===== LOOP =====
while True:
    get_swaps()
    time.sleep(20)
