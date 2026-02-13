import pandas

from pyfrbus.frbus import Frbus
from pyfrbus.sim_lib import sim_plot
from pyfrbus.load_data import load_data

import sympy
import builtins

# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models

# Load data
data = load_data("data/LONGBASE.TXT")

# Load model
frbus = Frbus("models/model.xml")

# 2. Define Simulation Window
start = "2023Q1"  # Ensure these match the index format in LONGBASE.TXT
end = "2030Q4"

# 3. CRITICAL: Initialize Tracking Residuals
# This ensures all model variables are mapped to symbols, not values
baseline_with_adds = frbus.init_trac(start, end, data)

# 1. Force headers to be uppercase strings
data.columns = [str(col).strip().upper() for col in data.columns]

# 2. Force the Index (Dates) to be strings (e.g., '2023Q1')
data.index = [str(idx).strip().upper() for idx in data.index]

# 3. Double-check: Is that ghost number a column name now?
ghost_val = "4.52193548387097"
if ghost_val in data.columns:
    print(f"🚨 FOUND IT: {ghost_val} is a column header. Renaming it to 'UNKNOWN_VAR'...")
    data = data.rename(columns={ghost_val: "UNKNOWN_VAR"})
    
# 3. Try the solve again with a cleaner namespace
opts = {'use_jac': False}

try:
    print("🚀 Attempting solve with numerical Jacobian...")
    sim = frbus.solve(start, end, baseline_with_adds, solver_opts=opts)
    sim.to_csv("results/output.csv")
    print("✅ Success! Results saved.")
except Exception as e:
    print(f"❌ Solver failed again: {e}")

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