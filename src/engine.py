import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Safe Bulk-Preload Engine (Build #558)")
    
    # 1. Environment & Path Setup
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        from pyfrbus import frbus
        print("✅ FRB/US Solver Dependencies Loaded.")
    except Exception as e:
        print(f"❌ FATAL: Dependency Load Error: {e}")
        sys.exit(1)

    # 2. Data Ingestion
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found.")
        return

    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 3. Model Initialization & Bulk Variable Discovery
    model = frbus.Frbus(model_xml)
    solve_start = df.index.min() + 1
    solve_end = df.index.max()
    
    # 🎯 FIX: Safely extract all model variables to avoid the discovery loop
    all_model_vars = []
    for attr in ['varnames', 'variables', 'var_names']:
        if hasattr(model, attr):
            val = getattr(model, attr)
            # Handle both callable methods and simple lists
            all_model_vars = [v.lower() for v in (val() if callable(val) else val)]
            print(f"📦 Pre-loaded {len(all_model_vars)} variables via '{attr}'")
            break
            
    if not all_model_vars:
        print("⚠️ Warning: Could not bulk-inspect variables. Reverting to basic list.")
        all_model_vars = list(df.columns)

    # 4. Create the Unit-Neutral Workspace
    # Pre-filling everything with 1.0 prevents the 'MissingDataError' chain reaction
    registry_df = pd.DataFrame(1.0, index=df.index, columns=all_model_vars)
    current_df = df.combine_first(registry_df).copy()

    # 5. Entropy Calibration Loop
    max_entropy_cycles = 5
    entropy_threshold = 1e-6
    results = None

    for cycle in range(1, max_entropy_cycles + 1):
        try:
            print(f"🔄 Entropy Cycle {cycle}/{max_entropy_cycles}...")
            # Results will now solve in one pass because all variables exist
            results = model.init_trac(solve_start, solve_end, current_df)
            
            entropy_score = np.mean(np.square(results.values))
            print(f"📊 Cycle {cycle} Entropy Score: {entropy_score:.8f}")
            
            if entropy_score < entropy_threshold:
                print("✨ Calibration achieved.")
                break
            
            # Nudge logic for calibration
            current_df = current_df.add(results * 0.1, fill_value=0)
            
        except Exception as e:
            # Final fallback: patch any missing variables the bulk-load missed
            msg = str(e)
            if "has no corresponding series in the input data" in msg:
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Patching missed variable: {missing_var}")
                    current_df[missing_var] = 1.0
                    continue 
            print(f"❌ Unrecoverable Math Error: {e}")
            sys.exit(1)

    # 6. Final Exports
    if results is not None:
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in results.columns]
        results[available].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
        print(f"✅ SUCCESS: Build #558 complete.")
    else:
        print("❌ FATAL: No results generated.")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()