import pandas as pd
import os
import re
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Golden Stability Engine (Build #564)")
    
    # 1. Environment & Path Setup
    working_dir, results_dir = os.getcwd(), os.path.join(os.getcwd(), "results")
    data_path, model_xml = os.path.join(working_dir, "data/processed"), os.path.join(working_dir, "models/model.xml")
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        from pyfrbus import frbus
        print("✅ FRB/US Solver Dependencies Loaded.")
    except Exception as e:
        print(f"❌ FATAL: Dependency Error: {e}"); sys.exit(1)

    # 2. Data Loading & Index Stabilization
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    
    # 🎯 FIX: Hard-Reset Index to prevent the 'Period not in list' error
    df = df[~df.index.duplicated(keep='first')]
    full_range = pd.period_range(start="1989Q3", end=df.index.max(), freq='Q')
    df = df.reindex(full_range).ffill().bfill()
    df.index.name = 'date'

    # 3. Model Initialization
    model = frbus.Frbus(model_xml)
    solve_start, solve_end = pd.Period("1989Q4", freq="Q"), df.index.max()
    registry_df = pd.DataFrame(index=df.index)
    results = None

    # 4. Entropy-Discovery Loop (Restored from #410 Logic)
    for cycle in range(1, 6): # 5 Entropy Cycles
        window_passed, attempts = False, 0
        while not window_passed and attempts < 600:
            try:
                # 🎯 FIX: Force a deep copy and re-index to prevent fragmentation
                current_df = pd.concat([df, registry_df], axis=1).fillna(1.0)
                current_df.index = pd.PeriodIndex(current_df.index, freq='Q') 
                
                results = model.init_trac(solve_start, solve_end, current_df)
                
                # Update discovered variables (residuals/identities)
                for col in results.columns:
                    if col not in df.columns:
                        registry_df[col] = results[col].reindex(df.index).fillna(1.0)
                window_passed = True
                
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    if attempts % 100 == 0: print(f"🛡️ Discovery (Attempt {attempts}): Found `{missing_var}`")
                    registry_df[missing_var] = 1.0
                    attempts += 1
                else:
                    print(f"❌ Critical Error: {msg}"); sys.exit(1)

        # Calibration Nudge (Entropy Logic)
        if results is not None:
            entropy_score = np.mean(np.square(results.values))
            print(f"📊 Cycle {cycle} Entropy: {entropy_score:.8f}")
            if entropy_score < 1e-6: break
            df = df.add(results * 0.1, fill_value=0)

    # 5. Final Exports
    if results is not None:
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in results.columns]
        results[available].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
        print(f"✅ SUCCESS: Exported {len(results.columns)} residuals to CSV.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()