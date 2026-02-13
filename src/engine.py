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

# 2. LOAD & ALIGN DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

# The 'dmptmax' patch
if 'dmptmax' not in data.columns:
    print("🩹 Patching missing 'dmptmax' with zeros...")
    data['dmptmax'] = 0.0

# 3. LOAD MODEL
frbus = Frbus("models/model.xml")

# 4. SCRUB THE GHOST (Using verified API names from Build #903)
ghost_str = "4.52193548387097"
print("🧹 Scrubbing variable lists...")
if hasattr(frbus, 'endo_names'):
    frbus.endo_names = [v for v in frbus.endo_names if str(v) != ghost_str]
if hasattr(frbus, 'exo_names'):
    frbus.exo_names = [v for v in frbus.exo_names if str(v) != ghost_str]

# 5. INITIALIZE & SOLVE
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Initializing Tracking...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Executing Solve...")
    sim = frbus.solve(start, end, baseline_with_adds)
    
    sim.to_csv("results/output.csv")
    print("✅ Success! Check Jenkins Artifacts.")
except Exception as e:
    print(f"❌ Execution Error: {e}")