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

original_xml = "models/model.xml"
fixed_xml = "models/model_fixed.xml"

print(f"🧹 Performing deep-math scan on {original_xml}...")
with open(original_xml, 'r') as f:
    content = f.read()

# Pattern 1: Find 140.18 / 31 and wrap it in parentheses to stop early evaluation
if "140.18" in content:
    print("🎯 Found potential numerator 140.18. Wrapping math expressions...")
    content = content.replace("140.18/31", "(140.18/31)")

# Pattern 2: Global protection for any decimal divided by 31 
# (Common in bond yield/RBBB logic)
content = re.sub(r'(\d+\.\d+)/31', r'(\1/31.0)', content)

with open(fixed_xml, 'w') as f:
    f.write(content)

# 2. RUN WITH GLOBAL SYMPY PATCH
# We also use a "Nuclear Option" on SymPy itself to ignore derivatives wrt numbers
import sympy
old_diff = sympy.diff
def robust_diff(f, *symbols, **kwargs):
    # Filter out any 'symbol' that looks like our ghost number
    clean_symbols = [s for s in symbols if str(s) != "4.52193548387097"]
    if not clean_symbols:
        return 0
    return old_diff(f, *clean_symbols, **kwargs)
sympy.diff = robust_diff

# 3. LOAD AND SOLVE
try:
    sys.path.append("/home/app/pyfrbus")
    from pyfrbus.load_data import load_data
    from pyfrbus.frbus import Frbus
    
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    frbus = Frbus(fixed_xml)
    print("🚀 Attempting solve with Math Protection...")
    
    baseline = frbus.init_trac("2023Q1", "2030Q4", data)
    sim = frbus.solve("2023Q1", "2030Q4", baseline)
    
    sim.to_csv("results/output.csv")
    print("✨ SUCCESS!")

except Exception as e:
    print(f"❌ FATAL: {e}")
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)