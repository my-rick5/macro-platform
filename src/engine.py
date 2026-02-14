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

original_xml = "models/model.xml"
fixed_xml = "models/model_fixed.xml"
ghost_str = "4.52193548387097"

print(f"🧹 Scanning {original_xml} for ghost literals...")
with open(original_xml, 'r') as f:
    content = f.read()

if ghost_str in content:
    print(f"🎯 Ghost found in XML! Neutralizing...")
    # Wrap the number in a way that the lexer won't mistake it for a variable name
    content = content.replace(ghost_str, f"({ghost_str})")
else:
    # If the number isn't there, it's being calculated from a fraction like 140.18/31
    # We will look for common day-count fractions and wrap them
    print("🔎 Ghost not found as string; checking for fractions (e.g., /31)...")
    content = re.sub(r'(\d+\.\d+/31)', r'(\1)', content)

with open(fixed_xml, 'w') as f:
    f.write(content)

# 2. LOAD WITH THE FIXED XML
try:
    sys.path.append("/home/app/pyfrbus")
    from pyfrbus.load_data import load_data
    from pyfrbus.frbus import Frbus
    
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    # LOAD THE REPAIRED XML
    print(f"🚀 Loading model from {fixed_xml}...")
    frbus = Frbus(fixed_xml)
    
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)