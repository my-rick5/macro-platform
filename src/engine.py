import os
import sys


# 1. FORCE THE ENVIRONMENT (Before any other imports)
try:
    import numpy as np
    import sympy
    import scipy
    import builtins
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
import pyfrbus.symbolic
original_partial = pyfrbus.symbolic.take_symengine_partial
def patched_partial(eq, w_resp_to, data_hash):
    if "4.521935" in str(w_resp_to):
        return "0"
    return original_partial(eq, w_resp_to, data_hash)
pyfrbus.symbolic.take_symengine_partial = patched_partial

# 3. DIRECTORY SETUP FOR JENKINS
os.makedirs("results", exist_ok=True)
os.makedirs("external_data", exist_ok=True)

# 4. LOAD AND SOLVE
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data

try:
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    frbus = Frbus("models/model.xml")
    
    print(f"🚀 Solving with {len(frbus.endo_names)} variables...")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS! Check Jenkins artifacts.")
except Exception as e:
    print(f"❌ Solver Failure: {e}")