from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
import pandas as pd


class StockService:

    def __init__(self, data_service, model=None):
        self.data_svc = data_service
        self.model = model

    def get_analysis(self, symbol: str,timeframe: str = "3mo"):
        df = self.data_svc.get_historical_data(symbol,timeframe)

        if df.empty:
            return {"error": f"No data for {symbol}"}

        # =========================
        # ✅ Normalize Close
        # =========================
        close_prices = df['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

        # =========================
        # 📊 INDICATORS
        # =========================

        # RSI
        rsi_series = RSIIndicator(close_prices).rsi()

        # EMA
        ema_series = EMAIndicator(close_prices, window=20).ema_indicator()

        # MACD
        macd_obj = MACD(close_prices)
        macd_series = macd_obj.macd()
        macd_signal_series = macd_obj.macd_signal()

        # Bollinger Bands
        bb = BollingerBands(close_prices)
        bb_high_series = bb.bollinger_hband()
        bb_low_series = bb.bollinger_lband()

        # =========================
        # 📌 Latest Values
        # =========================

        current_price = float(close_prices.iloc[-1])

        rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
        ema_val = float(ema_series.iloc[-1])

        macd_val = float(macd_series.iloc[-1])
        macd_signal = float(macd_signal_series.iloc[-1])

        bb_high = float(bb_high_series.iloc[-1])
        bb_low = float(bb_low_series.iloc[-1])

        # =========================
        # 🧠 SIGNAL LOGIC
        # =========================

        buy_conditions = [
            rsi_val < 30,
            current_price > ema_val,
            macd_val > macd_signal,
            current_price <= bb_low * 1.02
        ]

        sell_conditions = [
            rsi_val > 70,
            current_price < ema_val,
            macd_val < macd_signal,
            current_price >= bb_high * 0.98
        ]

        signal = "HOLD"
        confidence = 0

        if sum(buy_conditions) >= 3:
            signal = "BUY"
            confidence = sum(buy_conditions)

        elif sum(sell_conditions) >= 3:
            signal = "SELL"
            confidence = sum(sell_conditions)

        # =========================
        # 🤖 ML Prediction
        # =========================

        pred = None
        if self.model is not None and len(close_prices) >= 5:
            features = close_prices.tail(5).values.reshape(1, -1)
            pred = float(self.model.predict(features)[0])

        # =========================
        # 📊 PREPARE SERIES FOR UI
        # =========================

        return {
            "symbol": symbol,

            # Price data
            "prices": close_prices.tail(50).tolist(),
            "dates": df.index[-50:].strftime('%Y-%m-%d').tolist(),

            # Indicator values
            "rsi": round(rsi_val, 2),
            "ema": round(ema_val, 2),
            "macd": round(macd_val, 2),
            "macd_signal": round(macd_signal, 2),
            "bb_high": round(bb_high, 2),
            "bb_low": round(bb_low, 2),

            # Indicator series (🔥 IMPORTANT for charts)
            "ema_series": ema_series.tail(50).fillna(0).tolist(),
            "bb_high_series": bb_high_series.tail(50).fillna(0).tolist(),
            "bb_low_series": bb_low_series.tail(50).fillna(0).tolist(),
            "rsi_series": rsi_series.tail(50).fillna(50).tolist(),

            # Signals
            "signal": signal,
            "confidence": confidence,

            # ML
            "ml_prediction": round(pred, 2) if pred is not None else "N/A"
        }