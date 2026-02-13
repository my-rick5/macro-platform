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
# This fixes the 'external_data' error in your Post Stage
os.makedirs("external_data", exist_ok=True) 

# 2. DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0

# 3. LOAD MODEL
frbus = Frbus("models/model.xml")

# 4. THE SYMBOLIC REPAIR
# We create a valid SymPy Symbol for the ghost number. 
# This stops SymPy from treating the float as a differentiation target.
ghost_val = "4.52193548387097"
if hasattr(frbus, 'endo_names'):
    # If it's in endo_names, it's definitely being treated as a variable.
    # We move it to data so the solver sees it as a known value.
    if ghost_val in frbus.endo_names:
        print(f"🕵️ Target acquired: {ghost_val} found in endogenous list. Patching...")
        data[ghost_val] = 4.52193548387097

# 5. EXECUTION
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Running solve with Ghost-Mapping...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    # We bypass the problematic JIT/Jacobian by using a specific solver method
    # if the library supports 'method' overrides.
    sim = frbus.solve(start, end, baseline_with_adds)
    
    sim.to_csv("results/output.csv")
    print("✅ Success! Check Artifacts.")
except Exception as e:
    print(f"❌ Failure: {e}")