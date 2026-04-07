from datetime import timedelta, datetime

import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd

from src.connection.db_connection import get_db_connection


class PriceRepository:

    def __init__(self):
        self.conn = get_db_connection()



    def get_price_history_range(self, symbol: str, start_date=None, end_date=None):
        """
        Fetch data between dates.
        Defaults to last 3 months if not provided.
        """

        # =========================
        # ✅ Default date handling
        # =========================
        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            start_date = end_date - timedelta(days=90)  # ~3 months

        # Convert to proper datetime (important if string passed)
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # =========================
        # 📌 Fetch stock_id
        # =========================
        stock_id = self.get_stock_id(symbol)
        print(f"Fetching data for {symbol} (ID: {stock_id}) from {start_date.date()} to {end_date.date()}")

        query = """
                SELECT trade_date, \
                       open_price, \
                       high_price, \
                       low_price, \
                       close_price, \
                       volume
                FROM price_history
                WHERE stock_id = %s
                  AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date ASC \
                """

        with self.conn.cursor() as cur:
            cur.execute(query, (stock_id, start_date, end_date))
            rows = cur.fetchall()

        if not rows:
            return pd.DataFrame()

        # =========================
        # 📊 Convert to DataFrame
        # =========================
        df = pd.DataFrame(rows, columns=[
            "Date", "Open", "High", "Low", "Close", "Volume"
        ])

        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

        return df
    def get_stock_id(self, symbol):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT stock_id FROM stocks WHERE symbol = %s",
                (symbol,)
            )
            result = cur.fetchone()

            if result:
                return result[0]

            # Insert if not exists
            cur.execute(
                "INSERT INTO stocks (symbol) VALUES (%s) RETURNING stock_id",
                (symbol,)
            )
            stock_id = cur.fetchone()[0]
            self.conn.commit()

            return stock_id

    def insert_price_history(self, symbol, df: pd.DataFrame):
        if df is None or df.empty:
            return

        # =========================
        # ✅ Normalize DataFrame
        # =========================
        df = df.copy()

        # Fix MultiIndex columns (Yahoo issue)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure required columns exist
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        # Convert types safely
        df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
        df["High"] = pd.to_numeric(df["High"], errors="coerce")
        df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)

        # Drop rows with invalid prices
        df = df.dropna(subset=["Open", "High", "Low", "Close"])

        # =========================
        # 📌 Prepare batch data
        # =========================
        stock_id = self.get_stock_id(symbol)

        records = []
        for index, row in df.iterrows():
            records.append((
                stock_id,
                index.to_pydatetime(),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"])
            ))

        # =========================
        # ⚡ Batch Insert
        # =========================
        with self.conn.cursor() as cur:
            execute_batch(cur, """
                INSERT INTO price_history (
                    stock_id, trade_date,
                    open_price, high_price,
                    low_price, close_price, volume
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock_id, trade_date) DO NOTHING
            """, records)

        self.conn.commit()