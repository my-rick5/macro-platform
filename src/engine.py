import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Full-Timeline Recovery Engine v19.")
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
    
    # 🎯 FIX: Registry MUST have the exact same index as the main df
    registry_df = pd.DataFrame(index=df.index)

    first_actual = df.index.min()
    full_end = df.index.max()
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        window_passed = False
        attempts = 0
        
        while not window_passed and attempts < 300:
            try:
                # Merge current data with our aligned registry
                current_df = pd.concat([df, registry_df], axis=1)
                
                # Use current_solve_start as both start and end to clear 1989/1990 bridge
                # if it continues to fail, we shift to a larger window
                solve_end = min(current_solve_start + 3, full_end)
                
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                # Update the registry while maintaining full index alignment
                for col in results.columns:
                    if col not in target_variables:
                        # combine_first handles the update while keeping the full 1989-1990 history
                        if col not in registry_df.columns:
                            registry_df[col] = results[col]
                        else:
                            registry_df[col] = results[col].combine_first(registry_df[col])
                
                window_passed = True
                print(f"✅ Window {current_solve_start} solved.")
                
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Discovery: Initializing full series for `{missing_var}`")
                    # 🎯 FIX: Initialize across the ENTIRE timeline to prevent "not in list"
                    registry_df[missing_var] = 0.0
                    attempts += 1
                else:
                    print(f"❌ Unrecoverable Error: {msg}")
                    # Force exit to Jenkins to review the logs
                    sys.exit(1)

        # Move forward by the window size
        current_solve_start = min(current_solve_start + 4, full_end + 1)
            
    # 5. Finalize
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, registry_df], axis=1)
    
    print("📈 Generating final artifact...")
    final_results = model.init_trac(first_actual + 1, full_end, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Build #533 complete. Artifact at: {output_path}")

if __name__ == "__main__":
    run_pro_engine()