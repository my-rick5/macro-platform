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

# 1. SETUP DIRECTORIES (Ensures Post-Stage 'docker cp' works)
os.makedirs("results", exist_ok=True)

# 2. LOAD DATA & MODEL
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]
frbus = Frbus("models/model.xml")

# 3. THE "NUCLEAR" WORKAROUND
# Since the XML has a hard-coded float that breaks SymPy,
# we force the model to use numerical derivatives by hiding the Jacobian.
if hasattr(frbus, 'model'):
    print("🔧 Disabling analytic Jacobian to bypass SymPy constant error...")
    # This prevents the solver from trying to use the symbolic derivatives
    frbus.model.jacs = None 
    frbus.model.block_jacs = None

# 4. INITIALIZE & SOLVE
start, end = "2023Q1", "2030Q4"
try:
    print("🚀 Initializing Tracking...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Solving (Numerical Mode)...")
    # Call solve WITHOUT solver_opts to avoid the TypeError
    sim = frbus.solve(start, end, baseline_with_adds)
    
    sim.to_csv("results/output.csv")
    print("✅ Success! Results saved to artifacts.")
except Exception as e:
    print(f"❌ Final attempt failed: {e}")