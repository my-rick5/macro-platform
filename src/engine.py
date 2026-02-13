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
try:
    sim = frbus.solve(start, end, baseline_with_adds)
except ValueError as e:
    print(f"Solver failed. Error details: {e}")
    # FALLBACK: If the Jacobian is broken, try a non-derivative solver
    print("Attempting solve without analytic Jacobian...")
    sim = frbus.solve(start, end, baseline_with_adds, use_jac=False) 

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