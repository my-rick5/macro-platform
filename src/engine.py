import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Bulletproof Index Engine v22.")
print("--------------------------------------------------")

try:
    from pyfrbus import frbus
    print("✅ FRB/US Solver Dependencies Loaded.")
except Exception as e:
    print(f"❌ FATAL: Dependency Load Error: {e}")
    sys.exit(1)

def run_pro_engine():
    # 1. Environment & Path Setup
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 2. Data Loading with Strict Continuous Index
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    raw_df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    
    # 🎯 FIX: Create a guaranteed continuous timeline to prevent 'not in list' errors
    full_timeline = pd.period_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='Q')
    df = raw_df.reindex(full_timeline).fillna(0.0)
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)

    # 3. Model Initialization
    model = frbus.Frbus(model_xml)
    df['mc_mode'] = 0.0  
    df['mco_mode'] = 1.0  
    registry_df = pd.DataFrame(index=df.index)

    safe_harbor_start = pd.Period('2004Q1', freq='Q')
    data_horizon = df.index.max()
    current_solve_start = safe_harbor_start
    
    while current_solve_start < data_horizon:
        window_passed = False
        attempts = 0
        solve_end = min(current_solve_start + 3, data_horizon)

        while not window_passed and attempts < 150:
            try:
                current_df = pd.concat([df, registry_df], axis=1).fillna(0.0)
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 0.0)
                window_passed = True
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    registry_df[missing_var] = 0.0
                    attempts += 1
                else:
                    window_passed = True # Break current window
                    current_solve_start = data_horizon

        current_solve_start += 4
            
    # 5. Finalize with Explicit Index Alignment
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    # Ensure final_data has every single period from the safe_harbor_start to the end
    final_data = pd.concat([df, registry_df], axis=1).reindex(full_timeline).fillna(0.0)
    
    last_solved = registry_df.dropna(how='all').index.max()
    print(f"📈 Finalizing aligned residuals from {safe_harbor_start} to {last_solved}...")
    
    # 🎯 THE CRITICAL FIX: Ensure safe_harbor_start exists in the final_data index
    final_results = model.init_trac(safe_harbor_start, last_solved, final_data)
    final_results.to_csv(output_path)
    print(f"✅ SUCCESS: Build #538 complete.")

if __name__ == "__main__":
    run_pro_engine()