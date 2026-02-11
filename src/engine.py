import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Reverting to Build #410 Stability + Lite Export")
    
    # 1. Environment & Path Setup (Standard)
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Check dependencies
    try:
        from pyfrbus import frbus
        print("✅ FRB/US Solver Dependencies Loaded.")
    except Exception as e:
        print(f"❌ FATAL: Dependency Load Error: {e}")
        sys.exit(1)

    # 2. Data Loading (Simple & Robust)
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found.")
        sys.exit(1)

    # Standard concatenation used in #410
    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    
    # Normalize columns to lowercase
    df.columns = [c.lower() for c in df.columns]

    # 3. Model Solver (The #410 Logic)
    # No loops, no recursion, just a straight solve.
    model = frbus.Frbus(model_xml)
    solve_start = df.index.min() + 1
    solve_end = df.index.max()
    
    print(f"📈 Solving from {solve_start} to {solve_end}...")
    
    try:
        # The simple call that worked before we added complexity
        results = model.init_trac(solve_start, solve_end, df)
        print("✅ Solve complete.")
    except Exception as e:
        print(f"❌ Solver Failed: {e}")
        sys.exit(1)

    # 4. Final Exports
    # --- A. Full Export (The #410 Artifact) ---
    full_path = os.path.join(results_dir, "residuals.csv")
    results.to_csv(full_path)
    print(f"💾 Saved full residuals: {full_path}")

    # --- B. Lite Export (The New Requirement) ---
    lite_path = os.path.join(results_dir, "residuals_lite.csv")
    
    # The core estimates you asked for
    lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
    
    # Safety check: only export what actually exists
    available_vars = [v for v in lite_vars if v in results.columns]
    
    if available_vars:
        results[available_vars].to_csv(lite_path)
        print(f"💾 Saved lite residuals ({len(available_vars)} vars): {lite_path}")
    else:
        print("⚠️ Warning: No lite variables found in output.")

if __name__ == "__main__":
    run_pro_engine()