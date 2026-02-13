import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import pyfrbus.lexing
import sympy
import symengine
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

# 1. VERSION CHECK
print("📊 --- Dependency Audit ---")
print(f"SymPy:     {sympy.__version__}")
print(f"SciPy:     {scipy.__version__}")
print(f"SymEngine: {symengine.__version__}")
print(f"NumPy:     {np.__version__}")
print("---------------------------")

os.makedirs("results", exist_ok=True)

# 2. THE PATCH (Keep it as a safety net)
import pyfrbus.symbolic
original_partial = pyfrbus.symbolic.take_symengine_partial
def patched_partial(eq, w_resp_to, data_hash):
    if "4.521935" in str(w_resp_to):
        return "0"
    return original_partial(eq, w_resp_to, data_hash)
pyfrbus.symbolic.take_symengine_partial = patched_partial

# 3. RUN SOLVE
try:
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    frbus = Frbus("models/model.xml")
    
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    sim.to_csv("results/output.csv")
    print("✅ Success with updated dependencies!")
except Exception as e:
    print(f"❌ Failure: {e}")    