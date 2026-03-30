import yfinance as yf

from src.data_service.abstract_service import DataService


class YFinanceService(DataService):
    def get_historical_data(self, symbol: str):
        return yf.download(symbol, period="3mo")