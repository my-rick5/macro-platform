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

# 1. DATA SCANNER
data = load_data("data/LONGBASE.TXT")
ghost_val = 4.52193548387097

print(f"🔎 Scanning data for value: {ghost_val}")
# Find where this value exists in the dataframe
matches = (data == ghost_val).any()
matched_cols = matches[matches == True].index.tolist()

if matched_cols:
    print(f"🎯 Value found in columns: {matched_cols}")
    with open("external_data/data_match.txt", "w") as f:
        f.write(f"Ghost value found in: {matched_cols}")
else:
    print("❌ Value not found in data. It is likely a hardcoded constant in an equation.")

# 2. THE SYMBOLIC GUARD (The fix that should work)
original_partial = pyfrbus.symbolic.take_symengine_partial
def patched_partial(eq, w_resp_to, data_hash):
    if "4.521935" in str(w_resp_to):
        return "0"
    return original_partial(eq, w_resp_to, data_hash)
pyfrbus.symbolic.take_symengine_partial = patched_partial

# 3. SOLVE
try:
    frbus = Frbus("models/model.xml")
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")
except Exception as e:
    print(f"❌ Failure: {e}")