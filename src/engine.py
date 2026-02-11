import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Entropy-Restored Engine (Build #561)")
    
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

    # 2. Data Loading
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found.")
        sys.exit(1)

    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 3. Model Initialization
    model = frbus.Frbus(model_xml)
    solve_start = df.index.min() + 1
    solve_end = df.index.max()
    
    # Discovery Registry (To track what we find)
    registry_df = pd.DataFrame(index=df.index)
    target_variables = list(df.columns)
    
    # Entropy Calibration Settings
    max_entropy_cycles = 5
    entropy_threshold = 1e-6
    
    # 🎯 FIX: Initialize results safely
    results = None
    
    print(f"📈 Initializing Entropy-Discovery Loop: {solve_start} to {solve_end}")

    for cycle in range(1, max_entropy_cycles + 1):
        window_passed = False
        attempts = 0
        
        # 🎯 THE ENTROPY LOGIC: Recursive Discovery Loop
        # We set a high limit (500) because the model has many variables to initialize.
        while not window_passed and attempts < 500:
            try:
                # Merge base data with discovered variables
                current_df = pd.concat([df, registry_df], axis=1).fillna(1.0).copy()
                
                # Attempt to solve
                results = model.init_trac(solve_start, solve_end, current_df)
                
                # If successful, capture discovered variables for next pass
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 1.0)
                
                window_passed = True
                
            except Exception as e:
                msg = str(e)
                # 🛡️ CATCH & PATCH: Handle 'dmptmax' and other missing vars
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    if attempts % 10 == 0:
                        print(f"🛡️ Discovery (Attempt {attempts}): Initializing `{missing_var}`")
                    registry_df[missing_var] = 1.0
                    registry_df = registry_df.copy() # De-fragment
                    attempts += 1
                else:
                    print(f"❌ Unrecoverable Math Error in cycle {cycle}: {msg}")
                    sys.exit(1)

        # 🎯 ENTROPY CALIBRATION
        if results is not None:
            entropy_score = np.mean(np.square(results.values))
            print(f"📊 Cycle {cycle} Entropy Score: {entropy_score:.8f}")
            
            if entropy_score < entropy_threshold:
                print("✨ Calibration threshold met.")
                break
            
            # Nudge input data for next entropy cycle
            df = df.add(results * 0.1, fill_value=0)
        else:
            print("⚠️ Warning: Discovery phase failed to produce results.")
            break

    # 4. Final Exports (Including Lite Version)
    if results is not None:
        # Full Export
        full_path = os.path.join(results_dir, "residuals.csv")
        results.to_csv(full_path)
        
        # Lite Export
        lite_path = os.path.join(results_dir, "residuals_lite.csv")
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available_vars = [v for v in lite_vars if v in results.columns]
        results[available_vars].to_csv(lite_path)
        
        print(f"✅ SUCCESS: Exported residuals.csv and residuals_lite.csv")
    else:
        print("❌ FATAL: Engine failed to generate results.")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()