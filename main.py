import json

from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio
import math
from src.connection.db_connection import ensure_database, ensure_tables

from src.connection.connection_manager import ConnectionManager
from src.data_service.impl.yahoo_data_service import YFinanceService
from src.services.stock_service import StockService

import os
app = FastAPI()
manager = ConnectionManager()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

data_service = YFinanceService()
stock_service = StockService(data_service)



@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse(request=request,name="index.html")


@app.get("/stocks")
def get_stocks():
    return ["TCS.NS", "INFY.NS", "RELIANCE.NS"]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            symbol = payload.get("symbol")
            # Ensure symbol format is correct
            print(f"Received request for symbol: {symbol}")
            analysis = await asyncio.to_thread(
                stock_service.get_analysis, symbol
            )

            await websocket.send_json(sanitize(analysis))
    except Exception as e:
        print(f"Connection closed: {e}")
        manager.disconnect(websocket)

def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    return obj