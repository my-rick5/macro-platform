import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Full-History Recovery Engine v17.")
print("--------------------------------------------------")

try:
    from pyfrbus import frbus
    print("✅ FRB/US Solver Dependencies Loaded.")
except Exception as e:
    print(f"❌ FATAL: Dependency Load Error: {e}")
    sys.exit(1)

def run_pro_engine():
    # 1. Environment Setup
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
    
    # 🎯 FIX: Registry is a full-index DataFrame from the start
    registry_df = pd.DataFrame(0.0, index=df.index, columns=[])

    first_actual = df.index.min()
    full_end = df.index.max()
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        window_passed = False
        attempts = 0
        
        while not window_passed and attempts < 200:
            try:
                # 🛡️ Always provide the FULL history to satisfy lagged variables
                current_df = pd.concat([df, registry_df], axis=1)
                
                solve_end = current_solve_start if current_solve_start == pd.Period('1989Q4', freq='Q') else min(current_solve_start + 3, full_end)
                
                # Trac solve requires data covering the solve range + any required lags
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                # Update the registry with solved values to provide 'state' for the next window
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
                    print(f"🛡️ Discovery: Adding missing series `{missing_var}`")
                    registry_df[missing_var] = 0.0
                    attempts += 1
                else:
                    print(f"❌ Unrecoverable Numerical/Lag Error: {msg}")
                    # If it's a 'not in list' error, we likely have a date alignment issue in the CSVs
                    sys.exit(1)

        current_solve_start += 1 if current_solve_start == pd.Period('1989Q4', freq='Q') else 4
            
    # 5. Full-Sample Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, registry_df], axis=1)
    
    print("📈 Finalizing full-sample residuals...")
    final_results = model.init_trac(first_actual + 1, full_end, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Build #526 complete.")

if __name__ == "__main__":
    run_pro_engine()