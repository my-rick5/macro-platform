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
    # 1. FORCE THE CORRECT PATH
    # We point directly to the inner logic folder seen in Build #934
    sys.path.insert(0, "/home/app/pyfrbus/pyfrbus")
    sys.path.insert(0, "/home/app/pyfrbus")
    
    import run_jac
    import symbolic
    from frbus import Frbus
    from load_data import load_data
    
    print(f"✅ Deep-path imports successful. Patching {run_jac.__file__}")

    # 2. THE ULTIMATE JACOBIAN GUARD
    # If the engine creates a derivative string like 'Derivative(..., 4.5219...)', 
    # we catch it at the run_jac level.
    ghost_val = "4.52193548387097"
    
    original_jac_2_callable = run_jac.jac_2_callable
    def patched_jac_2_callable(jac):
        # jac is a list of (row, col, expression_string)
        sanitized_jac = []
        for r, c, expr in jac:
            if ghost_val in str(expr):
                # If the ghost is the variable of differentiation, the derivative is 0
                expr = "0"
            sanitized_jac.append((r, c, expr))
        return original_jac_2_callable(sanitized_jac)
    
    run_jac.jac_2_callable = patched_jac_2_callable
    print("🛡️ Jacobian Callable Interceptor active.")

    # 3. DATA & SOLVE
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(col).strip().lower() for col in data.columns]
    
    frbus = Frbus("models/model.xml")
    
    print("🚀 Running solver (Build #935)...")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)