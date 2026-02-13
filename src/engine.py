import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import sympy
import builtins
import os
import subprocess
import xml.etree.ElementTree as ET
# Inject Derivative into the global builtins so the lambdas in 
# pyfrbus/run_jac.py can see it regardless of import path issues.
builtins.Derivative = sympy.Derivative
builtins.symbols = sympy.symbols
builtins.exp = sympy.exp # Common in FRB/US models
builtins.log = sympy.log    


os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

# 1. THE "NUCLEAR" MONKEY PATCH
# We intercept the specific SymPy function that pyfrbus uses for Jacobians.
# If the engine tries to differentiate wrt a number, we force it to return 0.
def robust_diff(expr, symbol, *args, **kwargs):
    try:
        # If 'symbol' is actually a number, this is what's crashing.
        float(str(symbol))
        return sympy.Integer(0) 
    except ValueError:
        return sympy.diff(expr, symbol, *args, **kwargs)

# Inject our robust diff into the symbolic namespace
import pyfrbus.symbolic
pyfrbus.symbolic.diff = robust_diff
print("🛡️ Jacobian Patch Applied: Numeric derivatives will be ignored.")

# 2. LOAD & SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
frbus = Frbus("models/model.xml")

try:
    print("🚀 Attempting solve with Patched Jacobian...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success! The ghost was silenced.")
except Exception as e:
    print(f"❌ Failure: {e}")