import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data

# 1. Load Data
data = load_data("data/LONGBASE.TXT")

# 2. FORCE CASE INSENSITIVITY
# The model might be looking for lowercase 'dmptmax'
data.columns = [str(c).strip().lower() for c in data.columns]

# 3. DIAGNOSTIC: Check if dmptmax is missing
if 'dmptmax' not in data.columns:
    print("⚠️ Missing 'dmptmax' in data. Creating a zero-filled placeholder...")
    # Create a series of zeros so the model doesn't crash
    data['dmptmax'] = 0.0

# 4. Load Model and Initialize
frbus = Frbus("models/model.xml")
start, end = "2023Q1", "2030Q4"

try:
    print("🚀 Initializing Tracking (Round 2)...")
    baseline_with_adds = frbus.init_trac(start, end, data)
    
    print("🚀 Running Solver...")
    sim = frbus.solve(start, end, baseline_with_adds)
    sim.to_csv("results/output.csv")
    print("✅ Success!")
    
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    # Print the first 20 columns to see if names are mangled
    print(f"Available columns (first 20): {list(data.columns)[:20]}")