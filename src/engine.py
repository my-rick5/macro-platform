import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins

# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log

data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

# 3. PATCH MISSING SERIES
# We saw 'dmptmax' was missing in Build #891. 
# Let's ensure it and any others are there.
required_vars = ['dmptmax', 'dmptay', 'dmprr']
for v in required_vars:
    if v not in data.columns:
        print(f"⚠️ Patching missing variable: {v}")
        data[v] = 0.0

# 4. LOAD MODEL
frbus = Frbus("models/model.xml")
start, end = "2023Q1", "2030Q4"

# 5. INITIALIZE & SOLVE
try:
    print("🚀 Initializing Tracking...")
    # This is where the Derivative error was happening in #892
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Running Solver...")
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success! Check Artifacts.")
    
except Exception as e:
    print(f"❌ Failure: {e}")
    # Print a slightly longer list of columns to check for that ghost number
    print(f"Column Check: {list(data.columns)[20:40]}")