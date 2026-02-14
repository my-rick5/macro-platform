import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import os

# Create artifact directory
os.makedirs("results", exist_ok=True)

# --- 1. FRB/US "Staff" Forecast ---
data = load_data("data/LONGBASE.TXT")
frbus = Frbus("pyfrbus/models/model.xml")
start, end = pd.Period("2040Q1"), pd.Period("2040Q1") + 23

# Solve to baseline (this is the "Dude Forecast")
frbus_baseline = frbus.init_trac(start, end, data)
frbus_sim = frbus.solve(start, end, frbus_baseline)
with_adds = frbus.init_trac(start, end, data)
# --- 2. Pure Statistical (ARIMA) Forecast ---
# We take the historical GDP (xgdp) up to the start date
history = data.loc[:start-1, "xgdp"]

# Fit an ARIMA(2,1,0): 2 lags, 1 difference (to make it stationary), 0 moving avg
# This is a standard "statistical" approach to GDP
arima_model = ARIMA(history, order=(2, 1, 0))
arima_results = arima_model.fit()

# Forecast the same 24 quarters
arima_forecast = arima_results.get_forecast(steps=24).summary_frame()
arima_forecast.index = pd.period_range(start, end, freq='Q')

# --- 3. Save Artifacts ---
# Combine into one CSV for comparison
comparison_df = pd.DataFrame({
    "FRB_US_Forecast": frbus_sim["xgdp"],
    "ARIMA_Forecast": arima_forecast["mean"],
    "ARIMA_Lower_95": arima_forecast["mean_ci_lower"],
    "ARIMA_Upper_95": arima_forecast["mean_ci_upper"]
})
comparison_df.to_csv("results/forecast_comparison.csv")

# Generate Plot
plt.figure(figsize=(12, 6))
plt.plot(comparison_df.index.to_timestamp(), comparison_df["FRB_US_Forecast"], 
         label="FRB/US (Structural/Staff)", color='blue', linewidth=2)
plt.plot(comparison_df.index.to_timestamp(), comparison_df["ARIMA_Forecast"], 
         label="ARIMA (Statistical/Momentum)", color='red', linestyle='--')
plt.fill_between(comparison_df.index.to_timestamp(), 
                 comparison_df["ARIMA_Lower_95"], 
                 comparison_df["ARIMA_Upper_95"], color='red', alpha=0.1, label="ARIMA 95% CI")

plt.title("Economic Forecast: Structural (FRB/US) vs. Statistical (ARIMA)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("results/forecast_plot.png")
print("✅ Artifacts saved to ./results/")


# Select the variables you actually care about
vars_to_plot = ['rff', 'lur', 'pcepie', 'xgdp']
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

for i, var in enumerate(vars_to_plot):
    # Plot the baseline vs the simulation
    axes[i].plot(with_adds.index.to_timestamp(), with_adds[var], label='Baseline', color='gray', linestyle='--')
    axes[i].plot(frbus_sim.index.to_timestamp(), frbus_sim[var], label='Shock', color='blue')
    
    # 1. SCALE FIX: Set X-axis limits to your specific window
    axes[i].set_xlim(start.to_timestamp(), end.to_timestamp())
    
    # 2. SCALE FIX: Auto-scale Y-axis based ONLY on the data in that window
    # This prevents the "2175 steady state" from squishing the current data
    window_data = frbus_sim.loc[start:end, var]
    buffer = (window_data.max() - window_data.min()) * 0.1
    axes[i].set_ylim(window_data.min() - buffer, window_data.max() + buffer)
    
    axes[i].set_title(f'Variable: {var}')
    axes[i].legend()

plt.tight_layout()
plt.savefig("results/zoomed_sim_plot.png")