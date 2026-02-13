import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins
import os
import subprocess

# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log    


# 1. SETUP
os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

# 2. LOAD MODEL FIRST
frbus = Frbus("models/model.xml")

# 3. FILTER DATA BY MODEL NAMES
# We only keep columns that the model actually knows about.
# This prevents any "stray" numbers in the CSV from being read as variables.
raw_data = load_data("data/LONGBASE.TXT")
raw_data.columns = [str(c).strip().lower() for c in raw_data.columns]

# Get the list of all valid variables from the model API
valid_vars = set(frbus.endo_names) | set(frbus.exo_names)
print(f"📋 Model expects {len(valid_vars)} variables.")

# Keep only valid columns + the index
data = raw_data[[col for col in raw_data.columns if col in valid_vars]]

# 4. PATCH DMPTMAX (if still missing from the whitelist)
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0

# 5. SOLVE
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Solving with Strict Variable Whitelist...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success! Whitelisting blocked the ghost value.")
except Exception as e:
    print(f"❌ Failure: {e}")