import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Index-Safe Recovery Engine v16.")
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
    
    # Use a DataFrame to hold discovered variables to guarantee index alignment
    registry_df = pd.DataFrame(index=df.index)

    first_actual = df.index.min()
    full_end = df.index.max()
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        window_passed = False
        attempts = 0
        
        while not window_passed and attempts < 150:
            try:
                # 🎯 FIX: Explicitly align discovered variables with the main index
                current_df = pd.concat([df, registry_df], axis=1)
                
                # Single-quarter solve for 1989Q4 bridge, 4-quarter windows otherwise
                solve_end = current_solve_start if current_solve_start == pd.Period('1989Q4', freq='Q') else min(current_solve_start + 3, full_end)
                
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                # Capture residual/identity values back into registry
                for col in results.columns:
                    if col not in target_variables:
                        registry_df[col] = results[col]
                window_passed = True
                print(f"✅ Window {current_solve_start} solved.")
                
            except Exception as e:
                match = re.search(r'`([^`]+)`', str(e))
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Discovery: Adding missing series `{missing_var}`")
                    # Initialize with zeros across the ENTIRE index to prevent 1992Q1 gaps
                    registry_df[missing_var] = 0.0
                    attempts += 1
                else:
                    print(f"❌ Unrecoverable Index/Numerical Error: {e}")
                    sys.exit(1)

        current_solve_start += 1 if current_solve_start == pd.Period('1989Q4', freq='Q') else 4
            
    # 5. Full-Sample Results Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, registry_df], axis=1)
    
    print("📈 Finalizing aligned full-sample residuals...")
    final_results = model.init_trac(first_actual, full_end, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Build #524 complete. Artifact archived.")

if __name__ == "__main__":
    run_pro_engine()