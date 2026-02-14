import os
import sys


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
    # 2. CORRECT IMPORTS
    # Based on your file structure: /home/app/pyfrbus/pyfrbus/load_data.py
    from pyfrbus.load_data import load_data
    from pyfrbus.frbus import Frbus
    
    print("✅ All internal modules imported successfully.")

    # 3. APPLY THE SYMBOLIC GUARD (Our original fix for the ghost variable)
    original_partial = pyfrbus.symbolic.take_symengine_partial
    def patched_partial(eq, w_resp_to, data_hash):
        if "4.521935" in str(w_resp_to):
            return "0"
        return original_partial(eq, w_resp_to, data_hash)
    
    pyfrbus.symbolic.take_symengine_partial = patched_partial
    print("🛡️ Symbolic Guard active.")

    # 4. LOAD AND SOLVE
    # Path is 'data/LONGBASE.TXT' as seen in your ls -R log
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    frbus = Frbus("models/model.xml")
    
    print(f"🚀 Solving for range 2023Q1 to 2030Q4...")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL ERROR: {e}")
    # Write to external_data so Jenkins archives it
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)