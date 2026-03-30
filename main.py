from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.data_service.impl.yahoo_data_service import YFinanceService
from src.services.stock_service import StockService

app = FastAPI()
templates = Jinja2Templates(directory="templates")
data_service = YFinanceService()
stock_service = StockService(data_service)


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/stocks")
def get_stocks():
    return ["TCS.NS", "INFY.NS", "RELIANCE.NS"]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            symbol = await websocket.receive_text()
            # Ensure symbol format is correct
            symbol = symbol.upper() if "." in symbol else f"{symbol.upper()}.NS"

            # Use service to get all analysis
            analysis = stock_service.get_analysis(symbol)
            await websocket.send_json(analysis)
    except Exception as e:
        print(f"Connection closed: {e}")
