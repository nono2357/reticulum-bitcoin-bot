#!/usr/bin/env python3

import binascii
from datetime import datetime, timezone
import json
from lxmfy import LXMFBot, IconAppearance, pack_icon_appearance_field
import urllib.request
import requests

API_BASE_URL = "https://mempool.space/api"

def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read()

def get_current_datetime() -> str:
    current_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return current_utc

def get_bitcoin_info() -> dict:
    """
    Fetches the latest Bitcoin block number, its timestamp, and BTC price in USD
    using the mempool.space public API.

    Returns:
        dict with keys:
            - block_height     (int)
            - block_hash       (str)
            - block_timestamp  (int)  Unix timestamp
            - block_time_utc   (str)  Human-readable UTC time
            - btc_price_usd    (int)
    """

    current_utc = get_current_datetime()

    # 1. Latest block height (plain-text integer)
    block_height = int(fetch(f"{API_BASE_URL}/blocks/tip/height").decode().strip())

    # 2. Latest block hash (plain-text string)
    block_hash = fetch(f"{API_BASE_URL}/blocks/tip/hash").decode().strip()

    # 3. Block details → timestamp lives in block_data["timestamp"]
    block_data = json.loads(fetch(f"{API_BASE_URL}/block/{block_hash}"))
    block_timestamp = block_data["timestamp"]
    block_time_utc = datetime.fromtimestamp(
        block_timestamp, tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 4. Bitcoin price  →  {"time": ..., "USD": ..., "EUR": ..., ...}
    price_data = json.loads(fetch(f"{API_BASE_URL}/v1/prices"))
    btc_price_usd = price_data["USD"]

    d_info = {
        "current_utc":     current_utc,
        "block_height":    block_height,
        "block_hash":      block_hash,
        "block_timestamp": block_timestamp,
        "block_time_utc":  block_time_utc,
        "btc_price_usd":   btc_price_usd,
    }
    txt = \
    f"""
Current time: {d_info['current_utc']}
BTCUSD: {d_info['btc_price_usd']}
Last block - 
  height: {d_info['block_height']}
  hash: {d_info['block_hash']}
  time UTC: {d_info['block_time_utc']}
  timestamp: {d_info['block_timestamp']}
""".strip()
    print(txt)
    return txt

class ReticulumBitcoinBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="reticulum-bitcoin-bridge",
            announce=600,
            announce_immediately=True,
            announce_enabled=True,
            autopeer_propagation=True,
            command_prefix="/",
            rate_limit=10, # Allow 10 messages / minute
            first_message_enabled=True,
            hot_reloading=True,
        )
        icon_data = IconAppearance(
            #icon_name="currency_bitcoin",
            icon_name="hand-coin",
            fg_color=b'\xFF\xA5\x00',
            bg_color=b'\x33\x33\x33'   # Dark Grey
        )
        self.bot_icon_field = pack_icon_appearance_field(icon_data)
        self.setup_message_handlers()

    def run(self):
        self.bot.run()

    def setup_message_handlers(self):
        @self.bot.command(name="ping", description="Responds with pong")
        def ping_command(ctx):
            ctx.reply("pong", lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="time", description="Date&time")
        def ping_command(ctx):
            ctx.reply(get_current_datetime(), lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="info", description="Bitcoin network info")
        def info_command(ctx):
            ctx.reply(str(get_bitcoin_info()), lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="fees", description="Bitcoin fees")
        def fees_command(ctx):
            response = requests.get(f"{API_BASE_URL}/v1/fees/recommended")
            j = response.json()
            txt = f"low/med/high: {j['hourFee']} {j['halfHourFee']} {j['fastestFee']}"
            ctx.reply(txt, lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="broadcast", description="Broadcast a TX")
        def broadcast_command(ctx):
            txt = ' '.join(ctx.args)
            response = requests.post(f"{API_BASE_URL}/tx", headers={"Content-Type": "text/plain"}, data=txt)
            ctx.reply(response.text, lxmf_fields=self.bot_icon_field)

        #@self.bot.on_message()
        def fallback(self, sender, message):
            #ctx.reply(f"Unknown command. Try /help to start.", lxmf_fields=self.bot_icon_field)
            pass

if __name__ == "__main__":
    rbb = ReticulumBitcoinBot()
    print(f"Starting bot: {rbb.bot.config.name}")
    bot_address = binascii.hexlify(rbb.bot.local.hash).decode('utf-8')
    print(f"Bot LXMF Address: {bot_address}") # Prints the bot's address
    rbb.run()
