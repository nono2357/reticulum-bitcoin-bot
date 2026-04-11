#!/usr/bin/env python3
"""
Reticulum Bitcoin Bot — LXMF bot providing Bitcoin network info via mempool.space API.

Commands:
    /ping       — Responds with pong
    /time       — Current UTC date & time
    /info       — Bitcoin network info (price, last block)
    /fees       — Recommended fee rates (low/med/high)
    /broadcast  — Broadcast a signed raw transaction (hex)
"""

import binascii
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import logging

import requests
from lxmfy import LXMFBot, IconAppearance, pack_icon_appearance_field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = "https://mempool.space/api"
HTTP_TIMEOUT = 10  # seconds
RATE_LIMIT = 10    # messages per minute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch_json(path: str) -> dict:
    """GET *path* (relative to API_BASE_URL) and return parsed JSON."""
    url = f"{API_BASE_URL}/{path}"
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_text(path: str) -> str:
    """GET *path* (relative to API_BASE_URL) and return plain text."""
    url = f"{API_BASE_URL}/{path}"
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.text.strip()


def get_current_datetime() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_bitcoin_info() -> str:
    """
    Fetch latest Bitcoin block info and BTC/USD price in parallel.

    Returns a human-readable multi-line string.
    """
    current_utc = get_current_datetime()

    # Parallel fetching: block data and price are independent
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_block = pool.submit(_fetch_latest_block)
        future_price = pool.submit(fetch_json, "v1/prices")

        block_data = future_block.result()
        price_data = future_price.result()

    block_time_utc = datetime.fromtimestamp(
        block_data["timestamp"], tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    return (
        f"Current time: {current_utc}\n"
        f"BTCUSD: {price_data['USD']}\n"
        f"Last block -\n"
        f"  height: {block_data['height']}\n"
        f"  hash: {block_data['id']}\n"
        f"  time UTC: {block_time_utc}\n"
        f"  timestamp: {block_data['timestamp']}"
    )


def _fetch_latest_block() -> dict:
    """Return the full block object for the latest block."""
    block_hash = fetch_text("blocks/tip/hash")
    return fetch_json(f"block/{block_hash}")


def validate_hex(raw: str) -> bool:
    """Return True if *raw* is a valid hex string."""
    try:
        bytes.fromhex(raw)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------


class ReticulumBitcoinBot:
    def __init__(self):
        self.bot = LXMFBot(
            name="reticulum-bitcoin-bridge",
            announce=600,
            announce_immediately=True,
            announce_enabled=True,
            autopeer_propagation=True,
            command_prefix="/",
            rate_limit=RATE_LIMIT,
            first_message_enabled=True,
            hot_reloading=True,
        )

        icon_data = IconAppearance(
            icon_name="hand-coin",
            fg_color=b"\xFF\xA5\x00",
            bg_color=b"\x33\x33\x33",
        )
        self.bot_icon_field = pack_icon_appearance_field(icon_data)
        self._register_commands()

    # ---- commands ---------------------------------------------------------

    def _register_commands(self):
        @self.bot.command(name="ping", description="Responds with pong")
        def ping_command(ctx):
            ctx.reply("pong", lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="time", description="Date & time")
        def time_command(ctx):
            ctx.reply(get_current_datetime(), lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="info", description="Bitcoin network info")
        def info_command(ctx):
            try:
                txt = get_bitcoin_info()
            except Exception as e:
                log.exception("Failed to fetch bitcoin info")
                txt = f"Error fetching bitcoin info: {e}"
            ctx.reply(txt, lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="fees", description="Bitcoin fees")
        def fees_command(ctx):
            try:
                j = fetch_json("v1/fees/recommended")
                txt = f"low/med/high: {j['hourFee']} {j['halfHourFee']} {j['fastestFee']}"
            except Exception as e:
                log.exception("Failed to fetch fees")
                txt = f"Error fetching fees: {e}"
            ctx.reply(txt, lxmf_fields=self.bot_icon_field)

        @self.bot.command(name="broadcast", description="Broadcast a TX")
        def broadcast_command(ctx):
            raw_tx = " ".join(ctx.args).strip()
            if not raw_tx:
                ctx.reply(
                    "Usage: /broadcast <raw_tx_hex>",
                    lxmf_fields=self.bot_icon_field,
                )
                return

            if not validate_hex(raw_tx):
                ctx.reply(
                    "Invalid hex. Please provide a valid raw transaction.",
                    lxmf_fields=self.bot_icon_field,
                )
                return

            try:
                response = requests.post(
                    f"{API_BASE_URL}/tx",
                    headers={"Content-Type": "text/plain"},
                    data=raw_tx,
                    timeout=HTTP_TIMEOUT,
                )
                ctx.reply(response.text, lxmf_fields=self.bot_icon_field)
            except Exception as e:
                log.exception("Failed to broadcast TX")
                ctx.reply(f"Error broadcasting TX: {e}", lxmf_fields=self.bot_icon_field)

        @self.bot.on_message()
        def fallback(ctx):
            ctx.reply(
                "Unknown command. Try /help to start.",
                lxmf_fields=self.bot_icon_field,
            )

    # ---- run --------------------------------------------------------------

    def run(self):
        self.bot.run()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rbb = ReticulumBitcoinBot()
    log.info("Starting bot: %s", rbb.bot.config.name)
    bot_address = binascii.hexlify(rbb.bot.local.hash).decode("utf-8")
    log.info("Bot LXMF Address: %s", bot_address)
    rbb.run()
