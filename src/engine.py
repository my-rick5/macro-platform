import os
import sys
import re 


# 1. FORCE THE ENVIRONMENT (Before any other imports)
try:
    import numpy as np
    import sympy
    import scipy
    import builtins
    import pyfrbus.symbolic
    builtins.Derivative = sympy.Derivative
    builtins.symbols = sympy.symbols
    builtins.exp = sympy.exp # Common in FRB/US models
    builtins.log = sympy.log
    print(f"✅ Environment Check: NumPy {np.__version__} is active.")
except ImportError as e:
    print(f"🚨 CRITICAL MISSING DEPENDENCY: {e}")
    # In a containerized env, we want to fail fast if the base image is broken
    sys.exit(1)

# 2. THE PATCH (Our safety net for the specific ghost value)

os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

try:
    sys.path.append("/home/app/pyfrbus")
    from pyfrbus.frbus import Frbus
    from pyfrbus.load_data import load_data
    import pyfrbus.equations # This is where variable lists usually live
    
    # THE NUCLEAR GUARD: 
    # Intercept the 'get_rhs_vars' or equivalent function to filter numbers
    ghost_val = "4.52193548387097"
    
    if hasattr(pyfrbus.equations, 'get_rhs_vars'):
        original_get_vars = pyfrbus.equations.get_rhs_vars
        def patched_get_vars(*args, **kwargs):
            vars_set = original_get_vars(*args, **kwargs)
            # Remove the ghost number from the set of 'variables'
            if ghost_val in vars_set:
                print(f"🛡️ Filtering ghost variable from equation RHS: {ghost_val}")
                vars_set.remove(ghost_val)
            return vars_set
        pyfrbus.equations.get_rhs_vars = patched_get_vars

    # DATA & MODEL
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    frbus = Frbus("models/model.xml")
    
    print("🚀 Attempting solve with Variable-List Filtering...")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)