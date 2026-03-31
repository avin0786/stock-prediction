class DataService:
    def get_historical_data(self, symbol: str,timeframe: str = "3mo"):
        raise NotImplementedError