import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Restoration Engine v27 (Build #520-Spec).")
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
    
    # 2. Data Loading (Pure CSV alignment)
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
    
    # Registry starts empty - grows dynamically
    registry_df = pd.DataFrame(index=df.index)

    # 4. The Original Solve Loop
    first_actual = df.index.min()
    full_end = df.index.max()
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        window_passed = False
        attempts = 0
        
        while not window_passed and attempts < 150:
            try:
                current_df = pd.concat([df, registry_df], axis=1).copy()
                
                # The 1989Q4 bridge quarter logic that originally worked
                solve_end = current_solve_start if current_solve_start == pd.Period('1989Q4', freq='Q') else min(current_solve_start + 3, full_end)
                
                results = model.init_trac(current_solve_start, solve_end, current_df)
                
                for col in results.columns:
                    if col not in target_variables:
                        # Direct assignment for speed
                        registry_df[col] = results[col].combine_first(registry_df[col] if col in registry_df else 0.0)
                
                window_passed = True
                print(f"✅ Window {current_solve_start} solved.")
                
            except Exception as e:
                msg = str(e)
                match = re.search(r'`([^`]+)`', msg)
                if match:
                    missing_var = match.group(1).lower()
                    print(f"🛡️ Discovery: Reverting to 0.0-initialization for `{missing_var}`")
                    registry_df[missing_var] = 0.0
                    registry_df = registry_df.copy() # Prevent Fragmentation
                    attempts += 1
                else:
                    print(f"❌ Numerical Fault: {msg}")
                    sys.exit(1)

        current_solve_start += 1 if current_solve_start == pd.Period('1989Q4', freq='Q') else 4
            
    # 5. Full-Sample Results Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, registry_df], axis=1).copy()
    
    print("📈 Finalizing aligned full-sample residuals...")
    final_results = model.init_trac(first_actual + 1, full_end, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Restoration complete.")

if __name__ == "__main__":
    run_pro_engine()