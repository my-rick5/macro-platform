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

# 1. PATCH JACOBIAN.PY
# We wrap the create_jacobian function to filter out numeric 'variables'
original_create_jacobian = pyfrbus.jacobian.create_jacobian
ghost_val = "4.52193548387097"

def patched_create_jacobian(n_eqs, rhs_vars, exprs, data_hash):
    # Filter rhs_vars: remove any 'variable' that is actually our ghost number
    sanitized_rhs_vars = []
    for var_set in rhs_vars:
        # Create a new set excluding the ghost string
        clean_set = {v for v in var_set if v != ghost_val}
        sanitized_rhs_vars.append(clean_set)
    
    return original_create_jacobian(n_eqs, sanitized_rhs_vars, exprs, data_hash)

# Inject the patch into the library at runtime
pyfrbus.jacobian.create_jacobian = patched_create_jacobian
print("🛡️ jacobian.py interceptor active: Ghost variables will be ignored.")

# 2. LOAD & SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
frbus = Frbus("models/model.xml")

try:
    print("🚀 Attempting solve with Jacobian Variable Filtering...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")
except Exception as e:
    print(f"❌ Failure: {e}")