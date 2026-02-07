import yfinance as yf
import polars as pl
from datetime import datetime

def refresh_market_data():
    # 1. Pull current 'Ground Truth'
    # ^VIX = Volatility Index
    # ^IRX = 13-week Treasury Bill (Interest Rate Proxy)
    tickers = ["^VIX", "^IRX"]
    data = yf.download(tickers, period="1d", interval="1m")
    
    # Get the most recent valid prices
    latest_vix = data['Close']['^VIX'].dropna().iloc[-1]
    latest_ffr = data['Close']['^IRX'].dropna().iloc[-1]
    
    # 2. Structure for the Factory
    # We create a simple starting state that Spark will read
    df = pl.DataFrame({
        "timestamp": [datetime.now()],
        "vix_start": [float(latest_vix)],
        "ffr_start": [float(latest_ffr)]
    })
    
    # 3. Deliver to the Warehouse
    # Every factory run will look here to see where to 'start' the math
    path = "gs://macro-engine-warehouse-macroflow-486515/factory/supply_line/latest_state.parquet"
    df.write_parquet(path)
    
    print(f"📦 Supply Line Updated | VIX: {latest_vix:.2f} | FFR: {latest_ffr:.2f}")

if __name__ == "__main__":
    refresh_market_data()
