# 📈 AI-Powered Stock Analyzer

A real-time stock analysis application built with **FastAPI**, **WebSockets**, and **Scikit-Learn**. The app fetches live market data from Nifty 50 and other Indian stocks, calculates technical indicators (RSI), and provides price predictions using a Machine Learning model.

## 🚀 Features
- **Real-Time Streaming**: Uses WebSockets to push live price updates and signals to the UI.
- **Technical Analysis**: Built-in RSI (Relative Strength Index) calculation for BUY/SELL/HOLD signals.
- **ML Predictions**: Integrated Random Forest model to predict the next price based on recent trends.
- **Interactive Dashboard**: Clean HTML/JavaScript interface with live Chart.js visualization.
- **NSE Integration**: Automatically handles Indian stock suffixes (e.g., converts `INFY` to `INFY.NS`).

## 🛠️ Project Structure
```
.
├── src/
│   ├── data_service/
│   │   └── impl/
│   │       └── yahoo_data_service.py  # Data fetching via yfinance
│   └── services/
│       └── stock_service.py           # Core business logic (RSI + ML)
├── templates/
│   └── index.html                     # Frontend Dashboard
├── main.py                            # FastAPI Entry point & WebSockets
├── stock_model.pkl                    # Trained Scikit-Learn model
└── requirements.txt                   # Project dependencies
```

## 📦 Installation

### Clone the repository
```bash
git clone <your-repo-url>
cd <project-folder>
```

### Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install fastapi uvicorn yfinance pandas numpy scikit-learn joblib ta
```

## 🏃 Usage

### Initialize the ML Model
On the first run, the StockService will automatically generate a stock_model.pkl if it doesn't exist. To train a custom model with your own data, ensure your YFinanceService is active.

### Start the FastAPI Server
```bash
uvicorn main:app --reload
```

### Open the Dashboard
Go to http://127.0.0.1:8000 in your browser.

## 📊 Technical Details
- **Backend**: FastAPI (Python)
- **Data Source**: Yahoo Finance API (via yfinance)
- **Indicators**: ta library for RSI (Momentum)
- **Machine Learning**: scikit-learn Random Forest Regressor
- **Frontend**: Vanilla JS + Chart.js + WebSockets
