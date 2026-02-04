import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.vector_ar.var_model import VAR

def run_macro_model():
    # 1. Load Data
    con = duckdb.connect('data/macro_warehouse.db')
    df = con.sql("""
        SELECT date, fed_funds_rate, inflation_mom, real_gdp 
        FROM stg_fred_indicators 
        WHERE inflation_mom IS NOT NULL 
        ORDER BY date ASC
    """).df()
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 2. Transform (Log GDP for growth linearity)
    df['log_gdp'] = np.log(df['real_gdp'])
    model_data = df[['fed_funds_rate', 'inflation_mom', 'log_gdp']]
    
    # 3. Fit Model
    model = VAR(model_data)
    results = model.fit(maxlags=12, ic='aic')
    
    # --- VISUALIZATION 1: Impulse Response Functions ---
    # This shows the impact of a 1-standard-deviation shock
    irf = results.irf(24) 
    fig_irf = irf.plot(orth=True, impulse='fed_funds_rate')
    fig_irf.suptitle("Shock to Fed Funds: Impact on Macro Variables", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('notebooks/shock_analysis.png')
    print("Saved: notebooks/shock_analysis.png")

    # --- VISUALIZATION 2: Forecast ---
    lag_order = results.k_ar
    forecast_steps = 12
    forecast = results.forecast(model_data.values[-lag_order:], forecast_steps)
    
    # Create a date index for the forecast
    last_date = df.index[-1]
    forecast_index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_steps, freq='MS')
    forecast_df = pd.DataFrame(forecast, index=forecast_index, columns=model_data.columns)
    
    # Plotting Fed Funds Forecast
    plt.figure(figsize=(10, 6))
    plt.plot(df.index[-24:], df['fed_funds_rate'][-24:], label='Historical')
    plt.plot(forecast_df.index, forecast_df['fed_funds_rate'], label='Forecast', linestyle='--')
    plt.title("Fed Funds Rate: 12-Month Projection")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('notebooks/fed_funds_forecast.png')
    print("Saved: notebooks/fed_funds_forecast.png")

if __name__ == "__main__":
    run_macro_model()
