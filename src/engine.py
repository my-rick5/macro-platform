import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins
import os

# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log    

# 1. SETUP
os.makedirs("results", exist_ok=True)
# 2. LOAD DATA
# Force everything to string to prevent numeric "leaks"
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().upper() for c in data.columns]

# 3. INITIALIZE MODEL
# We point to the XML and ensure we aren't accidentally triggering MCE 
# unless specifically needed, as MCE uses more complex derivatives.
frbus = Frbus("models/model.xml", mce=None)

# 4. API-BASED REPAIR
# Instead of touching internals, we use the documented append_replace 
# to "overwrite" any equation that might be using the ghost number incorrectly.
# For now, let's just try to solve without the ghost in the namespace.
start, end = "2023Q1", "2030Q4"

try:
    print("🚀 Initializing tracking residuals...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Executing solve...")
    # The user guide notes that solve returns a new DataFrame
    sim = frbus.solve(start, end, baseline_with_adds)
    
    sim.to_csv("results/output.csv")
    print("✅ Success! Ghost Busted via API.")
    
except Exception as e:
    print(f"❌ API Error: {e}")
    # If it still fails, we will use the next build to inspect the Frbus object
    print(f"Available API Methods: {dir(frbus)}")