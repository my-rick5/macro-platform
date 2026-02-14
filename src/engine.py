import pandas as pd
import matplotlib.pyplot as plt
import os
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
from pyfrbus.sim_lib import sim_plot

# 1. Setup
os.makedirs("results", exist_ok=True)
data = load_data("data/LONGBASE.TXT")
frbus = Frbus("pyfrbus/models/model.xml")

start = pd.Period("2040Q1")
end = start + 23

# 2. Run the "Regular Forecast" (No Shocks)
# init_trac calculates the 'add factors' to match LONGBASE exactly
with_adds = frbus.init_trac(start, end, data)
sim = frbus.solve(start, end, with_adds)

# 3. Save Artifacts
# Save the full simulation dataframe to CSV
sim.to_csv("results/frbus_baseline_forecast.csv")

# Create the plot
# We use a standard matplotlib figure so we can save it
plt.figure(figsize=(10, 6))
sim_plot(with_adds, sim, start, end)
plt.suptitle(f"FRB/US Regular Forecast Baseline ({start} - {end})")
plt.savefig("results/baseline_plot.png", dpi=300)

print("✅ Baseline CSV and Plot archived in ./results/")