# Reticulum Bitcoin Bot

An LXMF bot for the [Reticulum](https://reticulum.network/) network that provides real-time Bitcoin network information via the [mempool.space](https://mempool.space) public API.

## Commands

| Command | Description |
|---|---|
| `/ping` | Responds with pong |
| `/time` | Current UTC date & time |
| `/info` | BTC/USD price + latest block details |
| `/fees` | Recommended fee rates (low / med / high sat/vB) |
| `/broadcast <hex>` | Broadcast a signed raw transaction |
| `/help` | List available commands |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 reticulum_bitcoin_bot.py
```

The bot will print its LXMF address on startup. Share this address so others can reach it on the Reticulum network.

## Dependencies

- [lxmfy](https://github.com/lxmfy/lxmfy) — LXMF bot framework
- [requests](https://docs.python-requests.org/) — HTTP client
- [mempool.space API](https://mempool.space/docs/api) — Bitcoin data (no API key required)

## License

MIT
