import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Entropy-Discovery Hybrid Engine (Build #553)")
    
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

    # 2. Data Loading (Stable Ingestion)
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found in data/processed")
        return

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
    
    # Discovery Registry to handle missing variables like dmptmax
    registry_df = pd.DataFrame(index=df.index)
    target_variables = list(df.columns)
    
    # Entropy Calibration Settings
    max_entropy_cycles = 5
    entropy_threshold = 1e-6
    
    print(f"📈 Initializing Hybrid solve: {solve_start} to {solve_end}")

    for cycle in range(1, max_entropy_cycles + 1):
        window_passed = False
        attempts = 0
        
        # Discovery loop within each entropy cycle to handle MissingDataErrors
        while not window_passed and attempts < 50:
            try:
                # Merge base data with discovered variables and de-fragment
                current_df = pd.concat([df, registry_df], axis=1).fillna(1.0).copy()
                
                print(f"🔄 Entropy Cycle {cycle}/{max_entropy_cycles} (Attempt {attempts})...")
                results = model.init_trac(solve_start, solve_end, current_df)
                
                # Capture and update discovered variables (residuals/identities)
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 1.0)
                
                window_passed = True
                
            except Exception as e:
                msg = str(e)
                # Catch MissingDataError for exogenous variables like 'dmptmax'
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Discovery: Initializing missing variable `{missing_var}`")
                    registry_df[missing_var] = 1.0
                    registry_df = registry_df.copy() # Stay de-fragmented
                    attempts += 1
                else:
                    print(f"❌ Unrecoverable Math Error in cycle {cycle}: {msg}")
                    sys.exit(1)

        # Calibration Step: Calculate Entropy (Mean Squared Residuals)
        entropy_score = np.mean(np.square(results.values))
        print(f"📊 Cycle {cycle} Entropy Score: {entropy_score:.8f}")
        
        if entropy_score < entropy_threshold:
            print("✨ Calibration threshold met.")
            break
            
        # Nudge input data for the next entropy cycle
        df = df.add(results * 0.1, fill_value=0)

    # 4. Final Exports
    full_path = os.path.join(results_dir, "residuals.csv")
    results.to_csv(full_path)
    
    lite_path = os.path.join(results_dir, "residuals_lite.csv")
    lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
    available_vars = [v for v in lite_vars if v in results.columns]
    results[available_vars].to_csv(lite_path)
    
    print(f"✅ SUCCESS: Exported residuals.csv and residuals_lite.csv")

if __name__ == "__main__":
    run_pro_engine()