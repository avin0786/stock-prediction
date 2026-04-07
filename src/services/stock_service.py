from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
import pandas as pd
from src.repository.price_history import PriceRepository


class StockService:

    def __init__(self, data_service, model=None):
        self.data_svc = data_service
        self.model = model
        self.price_repo = PriceRepository()

    def get_analysis(self, symbol: str):
        df = self.price_repo.get_price_history_range(symbol)

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
        rsi_series = RSIIndicator(close_prices).rsi()
        ema_series = EMAIndicator(close_prices, window=20).ema_indicator()

        macd_obj = MACD(close_prices)
        macd_series = macd_obj.macd()
        macd_signal_series = macd_obj.macd_signal()

        bb = BollingerBands(close_prices)
        bb_high_series = bb.bollinger_hband()
        bb_low_series = bb.bollinger_lband()

        # =========================
        # 📌 Latest Values (safe)
        # =========================
        def safe_float(val, default=0):
            return float(val) if pd.notna(val) else default

        current_price = safe_float(close_prices.iloc[-1])
        rsi_val = safe_float(rsi_series.iloc[-1], 50)
        ema_val = safe_float(ema_series.iloc[-1])
        macd_val = safe_float(macd_series.iloc[-1])
        macd_signal = safe_float(macd_signal_series.iloc[-1])
        bb_high = safe_float(bb_high_series.iloc[-1])
        bb_low = safe_float(bb_low_series.iloc[-1])

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
        # 📊 CLEAN SERIES FOR UI
        # =========================
        def clean_series(series, default=None):
            return [
                float(x) if pd.notna(x) else default
                for x in series
            ]

        # Ensure equal length (VERY IMPORTANT for chart)
        length = min(len(close_prices), 50)

        prices = clean_series(close_prices.tail(length))
        dates = df.index[-length:].strftime('%Y-%m-%d').tolist()

        ema_clean = clean_series(ema_series.tail(length))
        bb_high_clean = clean_series(bb_high_series.tail(length))
        bb_low_clean = clean_series(bb_low_series.tail(length))
        rsi_clean = clean_series(rsi_series.tail(length), 50)

        # =========================
        # 📦 FINAL RESPONSE
        # =========================
        return {
            "symbol": symbol,

            # Price data
            "prices": prices,
            "dates": dates,

            # Indicator values
            "rsi": round(rsi_val, 2),
            "ema": round(ema_val, 2),
            "macd": round(macd_val, 2),
            "macd_signal": round(macd_signal, 2),
            "bb_high": round(bb_high, 2),
            "bb_low": round(bb_low, 2),

            # Indicator series
            "ema_series": ema_clean,
            "bb_high_series": bb_high_clean,
            "bb_low_series": bb_low_clean,
            "rsi_series": rsi_clean,

            # Signals
            "signal": signal,
            "confidence": confidence,

            # ML
            "ml_prediction": round(pred, 2) if pred is not None else None
        }