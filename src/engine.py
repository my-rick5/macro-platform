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

# 2. THE EQUATION SCANNER
# We search the compiled equations for the ghost value
ghost_val = "4.52193548387097"
print(f"🔎 Scanning {len(frbus.lexed_eqs)} compiled equations for the ghost...")

for eq_name, formula in frbus.lexed_eqs.items():
    # formula is likely a string or a list of tokens
    if ghost_val in str(formula):
        print(f"🚨 TARGET FOUND in equation: {eq_name}")
        print(f"   Formula: {formula}")

# 3. THE "FORCE CONSTANT" FIX
# If the ghost is being treated as a variable, we move it to the 'constants' list
if hasattr(frbus, 'constants'):
    print(f"🛡️ Forcing {ghost_val} into the constants table...")
    frbus.constants[ghost_val] = 4.52193548387097

# 4. DATA & SOLVE
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

try:
    print("🚀 Attempting solve with constant-injection...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")