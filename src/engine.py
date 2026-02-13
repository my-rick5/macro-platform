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

# 1. SETUP (Fixes the Post-Stage 'docker cp' error)
os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

# 2. LOAD DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

# 3. THE GHOST FIX
# If the number 4.5219... is being used as a variable name in the equations,
# we must ensure it exists in our data as a column so the solver doesn't panic.
ghost_val = "4.52193548387097"
if ghost_val not in data.columns:
    data[ghost_val] = 4.52193548387097

# 4. LOAD MODEL
frbus = Frbus("models/model.xml")
start, end = "2023Q1", "2030Q4"

# 5. INITIALIZE TRACKING
baseline_with_adds = frbus.init_trac(start, end, data)

# 6. FORCE NUMERICAL JACOBIAN
# Since the analytic/symbolic derivative is what's crashing, we bypass it.
# We do this by telling the solver to use 'central' or 'forward' differences.
print("🚀 Attempting solve with numerical approximation...")
try:
    # We use solver_opts to tell the underlying scipy engine to skip the jacobian
    sim = frbus.solve(
        start, 
        end, 
        baseline_with_adds,
        solver_opts={'jac': False} # This forces numerical estimation
    )
    sim.to_csv("results/output.csv")
    print("✅ Success! Simulation Complete.")
except Exception as e:
    print(f"❌ Failure: {e}")