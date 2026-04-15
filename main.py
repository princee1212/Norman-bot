import requests
import time
import os
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

# Track token activity
token_tracker = defaultdict(set)  # Use set for efficiency instead of list
sent_signals = set()  # Track sent signals to avoid duplicates

# ===== TELEGRAM =====
def send_telegram(msg):
    """Send message to Telegram with error handling."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

# ===== GET SWAPS =====
def get_swaps():
    """Fetch and process swap data from Moralis API."""
    try:
        url = f"https://deep-index.moralis.io/api/v2/{PANCAKE_ROUTER}/erc20/transfers?chain=bsc"
        
        headers = {
            "accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Check for HTTP errors
        if response.status_code != 200:
            logger.error(f"Moralis API error: {response.status_code}")
            return
        
        # Validate JSON response
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("Failed to decode Moralis API response as JSON")
            return
        
        if "result" not in data:
            logger.warning("No 'result' key in Moralis API response")
            return
        
        for tx in data["result"][:30]:
            try:
                # Extract transaction data
                usd_value = float(tx.get("value_usd", 0))
                if usd_value < 10000:
                    continue
                
                token_name = tx.get("token_name", "Unknown")
                token_symbol = tx.get("token_symbol", "")
                contract = tx.get("address")
                buyer = tx.get("to_address")
                
                # Skip stablecoins
                if token_symbol in ["USDT", "USDC", "BUSD"]:
                    continue
                
                # Skip if missing critical data
                if not contract or not buyer:
                    continue
                
                # Track unique buyers per token
                token_tracker[contract].add(buyer)
                count = len(token_tracker[contract])
                
                # ===== SIGNAL LOGIC =====
                if count >= 3:
                    signal = "🔥 MULTI-WHALE ACCUMULATION"
                elif count == 2:
                    signal = "⚠️ BUILDING MOMENTUM"
                else:
                    signal = "🟡 SINGLE WHALE"
                
                # Only alert when meaningful and not already sent
                signal_key = f"{contract}_{count}"
                if count >= 2 and signal_key not in sent_signals:
                    message = f"""
🚨 NORMAN V3 SIGNAL

Token: {token_name} ({token_symbol})
Buy Size: ${usd_value:,.2f}
Contract: {contract}

Whale Buyers: {count}
Signal: {signal}

Chain: BNB (PancakeSwap)
"""
                    if send_telegram(message):
                        sent_signals.add(signal_key)
                    
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"Error processing transaction: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing transaction: {e}")
                continue
    
    except requests.exceptions.Timeout:
        logger.error("Moralis API request timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Moralis API request failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_swaps: {e}")

# ===== MAIN LOOP =====
if __name__ == "__main__":
    logger.info("Starting Norman Bot V3...")
    
    # Validate environment variables
    if not all([BOT_TOKEN, CHAT_ID, MORALIS_API_KEY]):
        logger.error("Missing required environment variables: BOT_TOKEN, CHAT_ID, MORALIS_API_KEY")
        exit(1)
    
    send_telegram("🚀 NORMAN V3 Bot started successfully!")
    
    try:
        while True:
            get_swaps()
            send_telegram("Heartbeat: Norman running ✅")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        send_telegram("🛑 NORMAN V3 Bot stopped")
    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}")
        send_telegram(f"❌ NORMAN V3 Bot crashed: {e}")
        raise