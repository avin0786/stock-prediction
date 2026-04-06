import json

from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio

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
            month = payload.get("month")
            year = payload.get("year")
            # Ensure symbol format is correct
            symbol = symbol.upper() if "." in symbol else f"{symbol.upper()}.NS"
            time  = f"{month}mo" if month else "3mo" # Default to 3 months if not provided

            analysis = await asyncio.to_thread(
                stock_service.get_analysis, symbol,timeframe=time
            )

            await websocket.send_json(analysis)
    except Exception as e:
        print(f"Connection closed: {e}")
        manager.disconnect(websocket)
