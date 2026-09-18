# Alpaca Live Trading Control Center

This is a separate repository for Alpaca live trading. It is intentionally **fail-closed** and ships with live execution disabled:

- `ALPACA_PAPER=false` is required.
- `TRADING_MODE=LIVE` is required.
- `ENABLE_LIVE_ORDERS=false` by default.
- `DRY_RUN=true` by default.
- `EMERGENCY_STOP=true` by default.
- Live order submission additionally requires an explicit confirmation checkbox in the dashboard.

## Critical warning

This project can be modified to submit real-money orders. It is a starter control center, not a production-grade unattended trading system. Before enabling live orders, independently review authentication, asset eligibility, market-data freshness, order sizing, stop-loss behavior, retries, idempotency, reconciliation, logging, monitoring, and emergency shutdown procedures.

Never commit API keys. Store them as private Render environment variables. Never put them in frontend JavaScript.

## Supported symbols

- Stocks: `GOOGL`, `MSFT`, `META`
- Crypto: `BTC/USD`, `ETH/USD`, `SOL/USD`

Verify tradability and asset properties against your Alpaca account before trading.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

Keep the following settings during initial testing:

```env
ALPACA_PAPER=false
TRADING_MODE=LIVE
ENABLE_LIVE_ORDERS=false
DRY_RUN=true
EMERGENCY_STOP=true
```

The dashboard will show account and quote errors until credentials are configured. Do not enable live execution just to make the dashboard load.

## Render deployment

Use a paid Render Web Service for the dashboard/API. This repository does not include a Background Worker or automatic strategy loop yet. That is deliberate: live unattended execution requires a separately reviewed worker with persistent state, reconnection logic, order reconciliation, and monitoring.

Build command:

```bash
pip install -r backend/requirements.txt
```

Start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Add the credentials and safety variables in Render's private Environment settings. Keep live execution disabled until the complete system has been reviewed.
