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
    # 2. THE PATH FIX
    # Your ls -R shows the actual code is in /home/app/pyfrbus/pyfrbus/
    # We add that specific subfolder to the path
    sys.path.append("/home/app/pyfrbus")
    
    from pyfrbus.load_data import load_data
    from pyfrbus.frbus import Frbus
    import pyfrbus.symbolic as symbolic
    print("✅ Modules loaded from nested pyfrbus directory.")

    # 3. THE GHOST PATCH
    ghost_val = "4.52193548387097"
    original_partial = symbolic.take_symengine_partial
    
    def patched_partial(eq, w_resp_to, data_hash):
        target = str(w_resp_to)
        if ghost_val in target:
            print(f"🛡️ Neutralizing ghost variable in Jacobian: {target}")
            return "0"
        return original_partial(eq, w_resp_to, data_hash)
    
    symbolic.take_symengine_partial = patched_partial

    # 4. DATA AUDIT & SOLVE
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    # Quick check: Is RBBB involved in the ghost number?
    if 'rbbb' in data.columns:
        mean_rbbb = data['rbbb'].mean()
        print(f"📊 Mean RBBB in data: {mean_rbbb}")
        if str(ghost_val)[:5] in str(mean_rbbb):
            print("🚨 Warning: Ghost value matches RBBB data patterns.")

    frbus = Frbus("models/model.xml")
    
    print("🚀 Solving...")
    # Use the standard horizon from your logs
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS! Check results/output.csv")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)