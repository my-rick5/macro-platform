import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data

# 1. Load Data and Model
data = load_data("data/LONGBASE.TXT")
frbus = Frbus("models/model.xml")

# 2. Define Simulation Window
start = "2023Q1"  # Ensure these match the index format in LONGBASE.TXT
end = "2030Q4"

# 3. CRITICAL: Initialize Tracking Residuals
# This ensures all model variables are mapped to symbols, not values
baseline_with_adds = frbus.init_trac(start, end, data)

# 4. Solve using the initialized baseline
sim = frbus.solve(start, end, baseline_with_adds)

# Specify dates
start = pandas.Period("2040Q1")
end = start + 23

# Standard configuration, use surplus ratio targeting
data.loc[start:end, "dfpdbt"] = 0
data.loc[start:end, "dfpsrp"] = 1

# Solve to baseline with adds
with_adds = frbus.init_trac(start, end, data)

# 100 bp monetary policy shock and solve
with_adds.loc[start, "rffintay_aerr"] += 0.5
sim = frbus.solve(start, end, with_adds)

# View results
sim_plot(with_adds, sim, start, end)