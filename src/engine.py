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

# 2. LOAD
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
frbus = Frbus("models/model.xml")

# 3. THE "DEEP EXORCISM"
# We are going to scan every single internal dictionary for this float
ghost_val = 4.52193548387097
ghost_str = "4.52193548387097"

def scrub_obj(obj):
    if hasattr(obj, 'endog'):
        obj.endog = [v for v in obj.endog if str(v) != ghost_str]
    if hasattr(obj, 'symbols'):
        # If the ghost is in the symbols dict, it's being treated as a variable
        if ghost_str in obj.symbols:
            print(f"🎯 Removing {ghost_str} from symbolic dictionary...")
            del obj.symbols[ghost_str]

if hasattr(frbus, 'model'):
    scrub_obj(frbus.model)
    # Recursively scrub blocks
    if hasattr(frbus.model, 'blocks'):
        for block in frbus.model.blocks:
            scrub_obj(block)

# 4. INITIALIZE
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Initializing Tracking...")
    # This is often where the first pass of symbol validation happens
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Final Solve Attempt...")
    # Force the use of the simplest possible solver 
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS! Ghost Busted.")
except Exception as e:
    print(f"❌ Failure: {e}")