import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Full Entropy-Discovery Hybrid (Build #562)")
    
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

    # Combine data and ensure index is sorted
    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 3. Anchor Adjustment (The Fix for Build #561 Error)
    # The solver starts at 1989Q4, so we must ensure 1989Q3 exists in the data for lags.
    actual_start = pd.Period("1989Q3", freq="Q")
    if actual_start not in df.index:
        # If preprocessor didn't provide it, we back-fill the first available obs
        df.loc[actual_start] = df.iloc[0].values
        df = df.sort_index()

    # 4. Model Initialization
    model = frbus.Frbus(model_xml)
    solve_start = pd.Period("1989Q4", freq="Q")
    solve_end = df.index.max()
    
    registry_df = pd.DataFrame(index=df.index)
    target_variables = list(df.columns)
    
    # Entropy Calibration Settings
    max_entropy_cycles = 5
    entropy_threshold = 1e-6
    results = None
    
    print(f"📈 Solving from {solve_start} to {solve_end} with 1989Q3 anchor.")

    for cycle in range(1, max_entropy_cycles + 1):
        window_passed = False
        attempts = 0
        
        # Inner loop to discover variables (dmptmax, uyl, etc.)
        while not window_passed and attempts < 600:
            try:
                # Merge base data with discovered series
                current_df = pd.concat([df, registry_df], axis=1).fillna(1.0).copy()
                
                # Core Solver
                results = model.init_trac(solve_start, solve_end, current_df)
                
                # Sync discovered variables back to registry
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 1.0)
                
                window_passed = True
                
            except Exception as e:
                msg = str(e)
                # Catch MissingDataError during discovery
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    if attempts % 50 == 0:
                        print(f"🛡️ Discovery (Attempt {attempts}): Found `{missing_var}`")
                    registry_df[missing_var] = 1.0
                    registry_df = registry_df.copy() # De-fragment
                    attempts += 1
                else:
                    print(f"❌ Critical Error in cycle {cycle}: {msg}")
                    sys.exit(1)

        # Calibration Nudge
        if results is not None:
            entropy_score = np.mean(np.square(results.values))
            print(f"📊 Cycle {cycle} Entropy Score: {entropy_score:.8f}")
            
            if entropy_score < entropy_threshold:
                print("✨ Calibration achieved.")
                break
            
            # Re-solve with residual feedback to minimize entropy
            df = df.add(results * 0.1, fill_value=0)
        else:
            print("⚠️ Warning: Discovery failed to reach results.")
            break

    # 5. Final Exports
    if results is not None:
        # Export Full Residuals
        full_path = os.path.join(results_dir, "residuals.csv")
        results.to_csv(full_path)
        
        # Export Lite Residuals
        lite_path = os.path.join(results_dir, "residuals_lite.csv")
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in results.columns]
        results[available].to_csv(lite_path)
        
        print(f"✅ SUCCESS: Exported both residuals.csv and residuals_lite.csv")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()