from multiprocessing.dummy import connection

import psycopg2
from psycopg2 import sql

DB_NAME = "stockdb"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5433"

db_conn= None

def get_db_connection():
    global db_conn
    if db_conn is not None:
        return db_conn
    else:
        db_conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    return db_conn


def ensure_database():
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"✅ Database '{DB_NAME}' created")
    else:
        print(f"✅ Database '{DB_NAME}' already exists")

    cur.close()


def ensure_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    queries = [

        # stocks
        """
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) UNIQUE NOT NULL,
            company_name TEXT,
            exchange VARCHAR(20)
        );
        """,

        # price history
        """
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            stock_id INT REFERENCES stocks(stock_id) ON DELETE CASCADE,
            trade_date TIMESTAMP NOT NULL,
            open_price NUMERIC,
            high_price NUMERIC,
            low_price NUMERIC,
            close_price NUMERIC,
            volume BIGINT,
            UNIQUE(stock_id, trade_date)
        );
        """,

        # transactions
        """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id SERIAL PRIMARY KEY,
            stock_id INT REFERENCES stocks(stock_id),
            transaction_type VARCHAR(4) CHECK (transaction_type IN ('BUY', 'SELL')),
            quantity INT NOT NULL,
            price_per_share NUMERIC NOT NULL,
            fees NUMERIC DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        # portfolio
        """
        CREATE TABLE IF NOT EXISTS portfolio (
            stock_id INT PRIMARY KEY REFERENCES stocks(stock_id),
            total_quantity INT NOT NULL,
            average_buy_price NUMERIC,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        # user subscriptions
        """
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INT,
            stock_id INT REFERENCES stocks(stock_id),
            UNIQUE(user_id, stock_id)
        );
        """
    ]

    for query in queries:
        cur.execute(query)



    conn.commit()
    cur.close()

    print("✅ All tables verified/created")


if __name__ == "__main__":
    ensure_database()
    ensure_tables()