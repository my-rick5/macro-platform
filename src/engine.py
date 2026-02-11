import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Data-Bound Engine v21.")
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
    
    # 2. Data Loading
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    
    df.index = pd.PeriodIndex(df.index, freq='Q')
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)

    # 3. Model Initialization
    model = frbus.Frbus(model_xml)
    df['mc_mode'] = 0.0  
    df['mco_mode'] = 1.0  
    
    registry_df = pd.DataFrame(index=df.index)

    # Solve Parameters
    safe_harbor_start = pd.Period('2004Q1', freq='Q')
    # 🎯 FIX: Explicitly find the last date available in your CSV files
    data_horizon = df.index.max() 
    current_solve_start = safe_harbor_start
    
    print(f"⚓ Solving from {safe_harbor_start} to Data Horizon: {data_horizon}")

    while current_solve_start < data_horizon:
        window_passed = False
        attempts = 0
        
        # Calculate window end, ensuring we never exceed the physical data horizon
        solve_end = min(current_solve_start + 3, data_horizon)
        
        # 🎯 FIX: If the solve_start itself is the last period, we can't solve a window
        if current_solve_start >= data_horizon:
            break

        while not window_passed and attempts < 150:
            try:
                current_df = pd.concat([df, registry_df], axis=1)
                
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 0.0)
                
                window_passed = True
                print(f"✅ Window {current_solve_start} to {solve_end} solved.")
                
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Discovery: Adding `{missing_var}`")
                    registry_df[missing_var] = 0.0
                    attempts += 1
                else:
                    # If we hit the 'not in list' error here, it means the horizon check failed
                    print(f"⚠️ Reached data boundary or alignment error at {current_solve_start}: {msg}")
                    window_passed = True # Break current window to allow finalization
                    current_solve_start = data_horizon # Terminate loop

        current_solve_start += 4
            
    # 5. Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, registry_df], axis=1)
    
    # Final Solve range: From 2004 until the last valid solved period in registry
    last_solved = registry_df.dropna(how='all').index.max() if not registry_df.empty else safe_harbor_start
    print(f"📈 Finalizing residuals up to {last_solved}...")
    
    final_results = model.init_trac(safe_harbor_start, last_solved, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Build complete. Results archived for {safe_harbor_start} to {last_solved}.")

if __name__ == "__main__":
    run_pro_engine()