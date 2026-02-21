# zlog_telegram

Telegram bridge component for the zlog suite.

This project polls Telegram bot updates and bridges messages to/from a SQL-backed IRC/log pipeline.

## Components

- `zlog_telegram.py` — Telegram API client + chat state handling
- `zlog_bridge.py` — DB polling loop that relays queued log lines to Telegram and processes inbound commands
- `reply.py` — Telegram message parsing helpers

## Environment

Create `.env` with:

- `DB_HOST`
- `DB_USERNAME`
- `DB_PASSWORD`
- `TOKEN` (Telegram bot token)
- `CHAT_ID` (target Telegram chat ID)

## Run

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python zlog_bridge.py
```

## Notes

- The current bridge expects tables like `push`, `inbound`, `inbound_log`, and `logs` in your SQL backend.
- This keeps existing behavior from the original Telepush project, with naming aligned to zlog suite.
