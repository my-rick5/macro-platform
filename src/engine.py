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

# 1. LOAD MODEL
frbus = Frbus("models/model.xml")

# 2. DIAGNOSTIC: Why 933?
# We print the first 50 variable names. If we see numbers here, 
# the model.xml parsing is definitely the culprit.
print(f"🧐 Inspecting variable list (Total: {len(frbus.endo_names)}):")
print(f"Sample: {frbus.endo_names[:50]}")

# 3. THE "GHOST" INTERCEPTION
ghost_str = "4.52193548387097"

# We check if the ghost is considered a variable and KILL IT
if ghost_str in frbus.endo_names:
    print(f"🎯 GHOST DETECTED in Endogenous list! Removing...")
    frbus.endo_names.remove(ghost_str)

if ghost_str in frbus.exo_names:
    print(f"🎯 GHOST DETECTED in Exogenous list! Removing...")
    frbus.exo_names.remove(ghost_str)

# 4. DATA ALIGNMENT
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
if 'dmptmax' not in data.columns:
    data['dmptmax'] = 0.0

# 5. SOLVE
try:
    print("🚀 Attempting solve with sanitized symbol table...")
    baseline_with_adds = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")