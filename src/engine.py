import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import pyfrbus.lexing
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

# 1. PATCH RUN_JAC.PY INTERNALS
original_jac_2_callable = pyfrbus.run_jac.jac_2_callable
ghost_val = "4.52193548387097"

def patched_jac_2_callable(jac):
    sanitized_jac = []
    for row, col, expr_str in jac:
        # If the ghost number is being treated as a variable in a derivative string
        # e.g., "Derivative(variable, 4.52193548387097)"
        # we strip it out or replace it with a constant 0.
        if ghost_val in expr_str:
            print(f"🩹 Sanitizing Jacobian string: {expr_str[:50]}...")
            # If the string is a derivative wrt the ghost, it should be 0
            if f", {ghost_val})" in expr_str:
                expr_str = "0"
        sanitized_jac.append((row, col, expr_str))
    
    return original_jac_2_callable(sanitized_jac)

# Inject the patch
pyfrbus.run_jac.jac_2_callable = patched_jac_2_callable
print("🛡️ run_jac.py string-interceptor active.")

# 2. LOAD & SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
frbus = Frbus("models/model.xml")

try:
    print("🚀 Running solve...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")
except Exception as e:
    print(f"❌ Failure: {e}")