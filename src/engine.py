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

# ... after init_trac ...

# # 1. Sanitize the internal endogenous variable list
# # This ensures no floats 'leaked' into the list of things to differentiate
# frbus.endog = [str(v) for v in frbus.endog if not isinstance(v, (int, float))]

# # 2. Check if the specific value is actually a variable value
# print(f"Checking if 4.5219... exists in current data slice...")
# current_val = data.loc[start, :].iloc[0] # Just a sample
# print(f"Sample data point: {current_val}")

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