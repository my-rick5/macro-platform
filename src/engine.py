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

# 2. LOAD & SANITIZE DATA
data = load_data("data/LONGBASE.TXT")
data.columns = [str(c).strip().lower() for c in data.columns]

# Ensure no NaNs are being passed as variable names
data = data.fillna(0.0)

# 3. LOAD MODEL
frbus = Frbus("models/model.xml")
start, end = "2023Q1", "2030Q4"

# 4. INITIALIZE TRACKING
baseline_with_adds = frbus.init_trac(start, end, data)

# 5. THE EXORCISM: Explicitly clean the solver's variable list
# We check the 'model' and 'equations' objects for any floating point 'names'
if hasattr(frbus, 'model'):
    print("🧹 Cleaning internal variable lists...")
    # This reaches into the core list of variables the solver is tracking
    frbus.model.endog = [v for v in frbus.model.endog if isinstance(v, str)]
    
    # If the ghost number is specifically in the list, this will kill it
    ghost = 4.52193548387097
    frbus.model.endog = [v for v in frbus.model.endog if v != ghost and v != str(ghost)]

# 6. SOLVE
try:
    print("🚀 Attempting final solve...")
    # Passing 'jit=False' sometimes helps if the compiled Jacobian is the culprit
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success!")
except Exception as e:
    print(f"❌ Failure: {e}")
    # DIAGNOSTIC: Search for the number in the equation symbols
    if hasattr(frbus, 'model'):
        print(f"Is ghost in endog? {str(ghost) in frbus.model.endog}")