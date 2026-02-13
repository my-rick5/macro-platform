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


os.makedirs("results", exist_ok=True)

# 1. THE "SYMPY" SHIELD
# We override the Symbol class to prevent it from creating symbols that are floats.
# This is a 'brute force' way to stop the engine from differentiating a number.
original_symbol = sympy.Symbol
def safe_symbol(name, **kwargs):
    try:
        float(name)
        # If the name can be a float, it's not a variable. Return a constant instead.
        return sympy.Float(name)
    except ValueError:
        return original_symbol(name, **kwargs)

sympy.Symbol = safe_symbol
print("🛡️ SymPy Shield Activated: Blocking numeric symbols.")

# 2. LOAD MODEL & DATA
frbus = Frbus("models/model.xml")
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0

# 3. SOLVE
try:
    print("🚀 Solving with Symbolic Shielding...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Success! The ghost was blocked at the symbolic layer.")
except Exception as e:
    print(f"❌ Failure: {e}")