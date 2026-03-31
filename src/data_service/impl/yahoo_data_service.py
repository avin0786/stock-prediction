import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class YFinanceService:

    def __init__(self):
        self.cache = {}
        self.cache_expiry = timedelta(minutes=5)

    def get_historical_data(self, symbol: str,timeframe: str = "3mo") -> pd.DataFrame:
        now = datetime.now()

        # Cache hit
        if symbol in self.cache:
            df, timestamp = self.cache[symbol]
            if now - timestamp < self.cache_expiry:
                return df

        # Fetch fresh data
        try:
            df = yf.download(symbol, period="3mo")

            if df.empty:
                return pd.DataFrame()

            self.cache[symbol] = (df, now)
            return df

        except Exception as e:
            print(f"Data fetch error: {e}")
            return pd.DataFrame()