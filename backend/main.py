import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)

API_KEY = os.getenv("ALPACA_API_KEY_ID", "")
API_SECRET = os.getenv("ALPACA_API_SECRET_KEY", "")
PAPER = os.getenv("ALPACA_PAPER", "false").lower() == "true"
TRADING_MODE = os.getenv("TRADING_MODE", "LIVE").upper()
ENABLE_LIVE_ORDERS = os.getenv("ENABLE_LIVE_ORDERS", "false").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
EMERGENCY_STOP = os.getenv("EMERGENCY_STOP", "true").lower() == "true"
MAX_ORDER_NOTIONAL = float(os.getenv("MAX_ORDER_NOTIONAL", "100"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "3"))

# This live project intentionally fails closed unless the operator explicitly configures it.
# Do not use this starter as a production unattended trading system without independent review.
if PAPER:
    TRADING_BASE_URL = "https://paper-api.alpaca.markets"
else:
    TRADING_BASE_URL = "https://api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"

SUPPORTED_ASSETS = {
    "GOOGL": "stock",
    "MSFT": "stock",
    "META": "stock",
    "BTC/USD": "crypto",
    "ETH/USD": "crypto",
    "SOL/USD": "crypto",
}

app = FastAPI(title="Alpaca Live Trading Control Center", version="0.1.0")
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "frontend")), name="static")


class OrderRequest(BaseModel):
    symbol: str
    side: str = Field(pattern="^(buy|sell)$")
    qty: str
    order_type: str = Field(default="market", pattern="^(market|limit|stop|stop_limit)$")
    time_in_force: str = Field(default="day")
    limit_price: float | None = None
    stop_price: float | None = None
    client_order_id: str | None = None
    confirm_live: bool = False


def headers() -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET,
        "Content-Type": "application/json",
    }


def ensure_credentials() -> None:
    if not API_KEY or not API_SECRET:
        raise HTTPException(status_code=503, detail="Alpaca credentials are not configured")


def ensure_live_guardrails(confirm_live: bool = False) -> None:
    if TRADING_MODE != "LIVE":
        raise HTTPException(status_code=403, detail="TRADING_MODE must be LIVE for this repository")
    if PAPER:
        raise HTTPException(status_code=403, detail="Paper endpoint detected; live repository requires ALPACA_PAPER=false")
    if not ENABLE_LIVE_ORDERS:
        raise HTTPException(status_code=403, detail="Live orders are disabled. Set ENABLE_LIVE_ORDERS=true privately after review.")
    if DRY_RUN:
        raise HTTPException(status_code=403, detail="DRY_RUN=true; no live orders can be submitted")
    if EMERGENCY_STOP:
        raise HTTPException(status_code=403, detail="Emergency stop is active")
    if not confirm_live:
        raise HTTPException(status_code=400, detail="Explicit live-order confirmation is required")


async def alpaca_get(url: str) -> Any:
    ensure_credentials()
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, headers=headers())
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text[:1000])
    return response.json()


@app.get("/")
def index():
    return FileResponse(os.path.join(ROOT_DIR, "frontend", "index.html"))


@app.get("/api/config")
def config():
    return {
        "repository_mode": "LIVE",
        "paper": PAPER,
        "dry_run": DRY_RUN,
        "live_orders_enabled": ENABLE_LIVE_ORDERS,
        "emergency_stop": EMERGENCY_STOP,
        "max_order_notional": MAX_ORDER_NOTIONAL,
        "max_open_positions": MAX_OPEN_POSITIONS,
        "max_trades_per_day": MAX_TRADES_PER_DAY,
        "symbols": list(SUPPORTED_ASSETS.keys()),
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/account")
async def account():
    return await alpaca_get(f"{TRADING_BASE_URL}/v2/account")


@app.get("/api/positions")
async def positions():
    return await alpaca_get(f"{TRADING_BASE_URL}/v2/positions")


@app.get("/api/orders")
async def orders():
    return await alpaca_get(f"{TRADING_BASE_URL}/v2/orders?status=all&limit=50&direction=desc")


@app.get("/api/assets/{symbol}")
async def asset(symbol: str):
    symbol = symbol.upper()
    if symbol not in SUPPORTED_ASSETS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    return await alpaca_get(f"{TRADING_BASE_URL}/v2/assets/{symbol.replace('/', '%2F')}")


@app.get("/api/quote/{symbol}")
async def quote(symbol: str):
    symbol = symbol.upper()
    if symbol not in SUPPORTED_ASSETS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    if SUPPORTED_ASSETS[symbol] == "crypto":
        url = f"{DATA_BASE_URL}/v1beta3/crypto/us/latest/quotes?symbols={symbol}"
    else:
        url = f"{DATA_BASE_URL}/v2/stocks/{symbol}/quotes/latest"
    return await alpaca_get(url)


@app.post("/api/orders")
async def submit_order(order: OrderRequest):
    symbol = order.symbol.upper()
    if symbol not in SUPPORTED_ASSETS:
        raise HTTPException(status_code=400, detail="Unsupported symbol")
    ensure_live_guardrails(order.confirm_live)

    try:
        qty = float(order.qty)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    if qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    if qty > MAX_ORDER_NOTIONAL and SUPPORTED_ASSETS[symbol] == "crypto":
        raise HTTPException(status_code=400, detail="Quantity exceeds configured safety limit")

    payload: dict[str, Any] = {
        "symbol": symbol,
        "side": order.side,
        "type": order.order_type,
        "qty": order.qty,
        "time_in_force": order.time_in_force,
    }
    if order.limit_price is not None:
        payload["limit_price"] = order.limit_price
    if order.stop_price is not None:
        payload["stop_price"] = order.stop_price
    if order.client_order_id:
        payload["client_order_id"] = order.client_order_id

    ensure_credentials()
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{TRADING_BASE_URL}/v2/orders", headers=headers(), json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text[:1000])
    return response.json()


@app.post("/api/emergency-stop")
def emergency_stop():
    # This endpoint is intentionally informational in the starter.
    # Set EMERGENCY_STOP=true in the hosting environment to disable execution.
    return {"message": "Set EMERGENCY_STOP=true in the server environment and redeploy/restart."}
