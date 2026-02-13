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

# 1. SETUP (Fixes the Post-Stage 'docker cp' error)
os.makedirs("results", exist_ok=True)
os.makedirs("debug_data", exist_ok=True)

# 2. LOAD DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0

# 3. THE "GHOST-BUSTING" INITIALIZATION
# We explicitly set mce=None to prevent forward-looking symbolic derivatives
# and we will attempt to disable any JIT compilation if the API allows.
frbus = Frbus("models/model.xml", mce=None)

# 4. MANUALLY CLEAR THE JACOBIAN CACHE
# Since 'jac' appeared in your dir(frbus) list, let's nullify it 
# to force the solver to stop using the broken symbolic one.
if hasattr(frbus, 'jac'):
    print("🗑️ Clearing symbolic Jacobian cache...")
    frbus.jac = None

# 5. INITIALIZE & SOLVE
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Initializing Tracking...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Solving (Bypassing Symbolic derivatives)...")
    # Some versions of pyfrbus use 'jit=False' or 'force_numpy=True'
    # We'll try the most stable call first.
    sim = frbus.solve(start, end, baseline_with_adds)
    
    sim.to_csv("results/output.csv")
    print("✅ Success! Simulation completed.")
except Exception as e:
    print(f"❌ Execution Error: {e}")