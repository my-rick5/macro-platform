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

# 2. EMERGENCY PATCH: Replace the number with a 1.0 (for testing)
# This will tell us if the rest of the model can solve without that specific value.
ghost_str = "4.52193548387097"

if hasattr(frbus, 'model'):
    print(f"🧹 Scrubbing {ghost_str} from symbolic lists...")
    # Filter the endogenous variable list
    if hasattr(frbus.model, 'endog'):
        frbus.model.endog = [v for v in frbus.model.endog if str(v) != ghost_str]
    
    # Check if the number snuck into the block ordering
    if hasattr(frbus.model, 'blocks'):
        for block in frbus.model.blocks:
            if hasattr(block, 'endog'):
                block.endog = [v for v in block.endog if str(v) != ghost_str]

# 3. RUN ENGINE AS NORMAL
# (Include your standard load_data, init_trac, and solve logic here)

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