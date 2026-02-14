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

# Select the variables you actually care about
vars_to_plot = ['rff', 'lur', 'pcepie', 'xgdp']
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

for i, var in enumerate(vars_to_plot):
    # Plot the baseline vs the simulation
    axes[i].plot(with_adds.index.to_timestamp(), with_adds[var], label='Baseline', color='gray', linestyle='--')
    axes[i].plot(sim.index.to_timestamp(), sim[var], label='Shock', color='blue')
    
    # 1. SCALE FIX: Set X-axis limits to your specific window
    axes[i].set_xlim(start.to_timestamp(), end.to_timestamp())
    
    # 2. SCALE FIX: Auto-scale Y-axis based ONLY on the data in that window
    # This prevents the "2175 steady state" from squishing the current data
    window_data = sim.loc[start:end, var]
    buffer = (window_data.max() - window_data.min()) * 0.1
    axes[i].set_ylim(window_data.min() - buffer, window_data.max() + buffer)
    
    axes[i].set_title(f'Variable: {var}')
    axes[i].legend()

plt.tight_layout()
plt.savefig("results/zoomed_sim_plot.png")