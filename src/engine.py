import os
import sys
import sympy


# 2. ENVIRONMENT COMPLIANCE CHECK
print(f"🕵️ SymPy Version: {sympy.__version__}")
if sympy.__version__ != "1.3":
    print("🚨 WARNING: Environment is non-compliant. Expected SymPy 1.3.")

try:
    # Set the path to the inner logic folder
    sys.path.insert(0, "/home/app/pyfrbus/pyfrbus")
    
    from frbus import Frbus
    from load_data import load_data
    
    # 3. DATA LOADING
    # Standardizing columns to lowercase handles many 'variable not found' issues
    data = load_data("data/LONGBASE.TXT")
    data.columns = [str(col).strip().lower() for col in data.columns]
    
    # 4. MODEL INITIALIZATION
    print("🚀 Loading Model...")
    frbus = Frbus("models/model.xml")
    
    # 5. SOLVE
    # Range based on your previous logs
    start_q, end_q = "2023Q1", "2030Q4"
    print(f"📈 Solving from {start_q} to {end_q}...")
    
    baseline = frbus.init_trac(start_q, end_q, data)
    sim = frbus.solve(start_q, end_q, baseline)
    
    # 6. EXPORT
    output_path = "results/output.csv"
    sim.to_csv(output_path)
    print(f"✨ SUCCESS! Results written to {output_path}")

except Exception as e:
    print(f"❌ FATAL ERROR: {e}")
    # Persistent log for Jenkins to archive
    with open("external_data/failure_log.txt", "w") as f:
        f.write(str(e))
    sys.exit(1)