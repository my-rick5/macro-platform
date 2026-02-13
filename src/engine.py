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

# 1. LOAD MODEL
frbus = Frbus("models/model.xml")

# 2. FIXED EQUATION SCANNER
ghost_val = "4.52193548387097"
print(f"🔎 Scanning {len(frbus.lexed_eqs)} compiled equations...")

# Since lexed_eqs is a list, we enumerate it
for i, formula in enumerate(frbus.lexed_eqs):
    formula_str = str(formula)
    if ghost_val in formula_str:
        # We try to identify the variable associated with this index
        var_name = frbus.endo_names[i] if i < len(frbus.endo_names) else "Unknown"
        print(f"🚨 TARGET FOUND in Equation Index {i} (Associated Var: {var_name})")
        print(f"   Formula snippet: {formula_str[:100]}...")

# 3. THE "SYMBOLIC SURGERY"
# We forcibly remove the ghost from endo_names and exo_names if it's there
# and ensure it's in the constants dictionary.
for attr in ['endo_names', 'exo_names']:
    if hasattr(frbus, attr):
        current_list = getattr(frbus, attr)
        if ghost_val in current_list:
            print(f"✂️ Removing ghost from {attr}...")
            setattr(frbus, attr, [v for v in current_list if str(v) != ghost_val])

if hasattr(frbus, 'constants'):
    print(f"💎 Pinning {ghost_val} as a fixed constant...")
    frbus.constants[ghost_val] = 4.52193548387097

# 4. SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

try:
    print("🚀 Attempting final solve sequence...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")