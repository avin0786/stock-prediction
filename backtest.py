import backtrader as bt
import yfinance as yf
import pandas as pd


# =========================
# 📊 STRATEGY
# =========================

class EMACrossoverStrategy(bt.Strategy):

    params = dict(
        fast=10,
        slow=20,
        risk_per_trade=0.02,   # 2% capital risk
        stop_loss_pct=0.03,    # 3% stop loss
        reward_ratio=2         # Risk:Reward = 1:2
    )

    def __init__(self):
        self.ema_fast = bt.ind.EMA(self.data.close, period=self.p.fast)
        self.ema_slow = bt.ind.EMA(self.data.close, period=self.p.slow)

        self.crossover = bt.ind.CrossOver(self.ema_fast, self.ema_slow)

        self.order = None

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f"{dt} - {txt}")

    def next(self):

        # Debug (optional)
        # self.log(f"Close: {self.data.close[0]:.2f}")

        if self.order:
            return

        # =========================
        # 🟢 BUY LOGIC
        # =========================
        if not self.position:
            if self.crossover > 0:

                size = self.calculate_position_size()

                price = self.data.close[0]
                stop_price = price * (1 - self.p.stop_loss_pct)
                target_price = price * (1 + self.p.stop_loss_pct * self.p.reward_ratio)

                self.log(f"BUY signal at {price:.2f}")

                self.order = self.buy_bracket(
                    size=size,
                    price=price,
                    stopprice=stop_price,
                    limitprice=target_price
                )

        # =========================
        # 🔴 SELL LOGIC
        # =========================
        elif self.position:
            if self.crossover < 0:
                self.log(f"EXIT signal at {self.data.close[0]:.2f}")
                self.close()

    # =========================
    # 💰 POSITION SIZING
    # =========================
    def calculate_position_size(self):
        cash = self.broker.get_cash()
        price = self.data.close[0]

        risk_amount = cash * self.p.risk_per_trade
        stop_loss_amount = price * self.p.stop_loss_pct

        size = risk_amount / stop_loss_amount
        return max(int(size), 1)

    # =========================
    # 📢 ORDER NOTIFICATIONS
    # =========================
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED @ {order.executed.price:.2f}")
            else:
                self.log(f"SELL EXECUTED @ {order.executed.price:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Failed")

        self.order = None

    # =========================
    # 📊 TRADE RESULTS
    # =========================
    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"PROFIT: {trade.pnl:.2f}")


# =========================
# 📊 DATA LOADER
# =========================

def get_data(symbol="RELIANCE.NS"):
    df = yf.download(symbol, period="1y")  # more data

    # Fix MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep required columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

    # Lowercase for Backtrader
    df.columns = [col.lower() for col in df.columns]

    df.dropna(inplace=True)

    return bt.feeds.PandasData(dataname=df)


# =========================
# 🚀 BACKTEST RUNNER
# =========================

def run_backtest():
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(EMACrossoverStrategy)

    # Add data
    data = get_data()
    cerebro.adddata(data)

    # Initial capital
    cerebro.broker.setcash(100000)

    # Commission (0.1%)
    cerebro.broker.setcommission(commission=0.001)

    # Slippage (0.1%)
    cerebro.broker.set_slippage_perc(perc=0.001)

    # =========================
    # 📊 ANALYZERS
    # =========================
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    print("Starting Portfolio Value:", cerebro.broker.getvalue())

    results = cerebro.run()
    strat = results[0]

    print("Final Portfolio Value:", cerebro.broker.getvalue())

    # =========================
    # 📈 METRICS
    # =========================
    print("Sharpe Ratio:", strat.analyzers.sharpe.get_analysis())
    print("Drawdown:", strat.analyzers.drawdown.get_analysis())

    # Plot
    cerebro.plot()


# =========================
# ▶️ RUN
# =========================

if __name__ == "__main__":
    run_backtest()