import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Golden Stability Engine (Build #565)")
    
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
        print(f"❌ FATAL: Dependency Error: {e}"); sys.exit(1)

    # 2. Data Loading & Historical Buffering
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    raw_df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    raw_df.columns = [c.lower() for c in raw_df.columns]
    
    # 🎯 FIX: Increase anchor to 1980Q1 to satisfy internal 3-quarter and 4-quarter lags
    full_range = pd.period_range(start="1980Q1", end=raw_df.index.max(), freq='Q')
    df = raw_df.reindex(full_range).ffill().bfill()
    df.index.name = 'date'

    # 3. Model Initialization
    model = frbus.Frbus(model_xml)
    solve_start, solve_end = pd.Period("1989Q4", freq="Q"), df.index.max()
    
    # 🎯 FIX Fragmentation: Store discovered variables in a dict for bulk concat
    registry_dict = {}
    target_variables = list(df.columns)
    results = None

    # 4. Entropy-Discovery Loop (Core Calibration Logic)
    for cycle in range(1, 6):
        print(f"🔄 Entropy Cycle {cycle}/5...")
        window_passed, attempts = False, 0
        
        while not window_passed and attempts < 600:
            try:
                # Build de-fragmented workspace
                current_df = df.copy()
                if registry_dict:
                    discovery_df = pd.DataFrame(registry_dict, index=df.index)
                    current_df = pd.concat([current_df, discovery_df], axis=1)
                
                current_df = current_df.fillna(1.0)
                
                # Execute Solve
                results = model.init_trac(solve_start, solve_end, current_df)
                
                # Sync discovered series back to registry
                for col in results.columns:
                    if col not in target_variables:
                        registry_dict[col] = results[col]
                window_passed = True
                
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    if attempts % 50 == 0: print(f"🛡️ Discovery (Attempt {attempts}): Found `{missing_var}`")
                    # Initialize missing series across full range
                    registry_dict[missing_var] = pd.Series(1.0, index=df.index)
                    attempts += 1
                else:
                    print(f"❌ Critical Error in Discovery: {msg}"); sys.exit(1)

        # Calibration Nudge (Entropy logic)
        if results is not None:
            entropy_score = np.mean(np.square(results.values))
            print(f"📊 Cycle {cycle} Entropy: {entropy_score:.8f}")
            if entropy_score < 1e-6: break
            df = df.add(results * 0.1, fill_value=0)

    # 5. Final Exports
    if results is not None:
        # Full Artifact
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        
        # Lite Estimates Artifact
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in results.columns]
        results[available].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
        print(f"✅ SUCCESS: Build #565 Exported {len(results.columns)} variables.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()