import os
import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data

# 1. Setup results dir immediately
os.makedirs("results", exist_ok=True)

# 2. Load Data
data = load_data("data/LONGBASE.TXT")

# 3. FORCE EVERYTHING TO STRING
# This handles cases like D83 being read as a number if the 'A' is missing
data.columns = [str(c).strip().upper() for c in data.columns]

# 4. Load Model
frbus = Frbus("models/model.xml")
start, end = "2023Q1", "2030Q4"

# 5. INITIALIZE TRACKING
baseline_with_adds = frbus.init_trac(start, end, data)

# 6. THE FIX: Force the model's internal variable list to be pure strings
# If 'D83' somehow became the number 83.0 internally, this converts it back.
if hasattr(frbus, 'model'):
    # Iterate through the endogenous variables and force string type
    frbus.model.endog = [str(v) for v in frbus.model.endog]
    print(f"✅ Sanitized {len(frbus.model.endog)} variables to string format.")

# 7. SOLVE
try:
    print(f"🚀 Solving from {start} to {end}...")
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✨ Simulation successful!")
except Exception as e:
    print(f"❌ Solver failed: {e}")
    # Final diagnostic: is the ghost number actually one of your variables?
    if "4.5219" in str(e):
        print("🔍 Investigation: The number 4.5219... is being used as a variable name.")
        # Check if D79A, D83, etc. are currently mapping to that value