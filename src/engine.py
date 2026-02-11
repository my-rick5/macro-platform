import pandas as pd
import os
import re
import sys
import numpy as np

print("--------------------------------------------------")
print("🚀 Heartbeat: Unified Positional Reset Engine.")
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
    
    # Corrected 'exist_ok' for directory safety
    os.makedirs(results_dir, exist_ok=True)
    
    # 2. Data Loading & Indexing
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No source CSVs found.")
        return

    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') 
        for f in files
    ], axis=1).sort_index()
    
    df.index = pd.PeriodIndex(df.index, freq='Q')
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)

    # 3. Model Parameters
    model = frbus.Frbus(model_xml)
    solver_params = {
        'max_iter': 1000, 
        'tolerance': 1e-3,
        'debug': True,
        'show_failed': 5
    }
    
    # Mode flags for expectations
    df['mc_mode'] = 0.0  
    df['mco_mode'] = 1.0  

    first_actual = df.index.min()
    full_end = df.index.max()
    missing_registry = {}

    def get_identity_locked_proxy(var_name):
        if var_name not in target_variables: return None 
        return df[var_name].iloc[0]

    # 4. Iterative Solve Logic
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        # 🎯 STRATEGY: POSITIONAL RESET (BYPASS 1989Q4 SINGULARITY)
        if current_solve_start == pd.Period('1989Q4', freq='Q'):
            print("🛡️ 1989Q4 Deadlock: Triggering Positional State Reset...")
            current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
            
            # Using positional arguments (start, end, data, options) to avoid 'init' keyword error
            # Identical start/end bypasses the Jacobian transition matrix collapse.
            results = model.init_trac(current_solve_start, current_solve_start, current_df, solver_params)
            
            for col in results.columns:
                if col not in target_variables:
                    missing_registry[col] = float(results[col].iloc[-1])
            window_passed = True
            
        else:
            # Standard windowing for 1990+
            step_size = 1 if current_solve_start < pd.Period('1991Q1', freq='Q') else 4
            current_solve_end = min(current_solve_start + (step_size - 1), full_end)
            
            window_passed = False
            window_attempts = 0
            while not window_passed and window_attempts < 50:
                try:
                    current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
                    results = model.init_trac(current_solve_start, current_solve_end, current_df, solver_params)
                    
                    for col in results.columns:
                        if col not in target_variables:
                            missing_registry[col] = float(results[col].iloc[-1])
                    window_passed = True
                except Exception as e:
                    match = re.search(r'`([^`]+)`', str(e) or "")
                    if match:
                        var = match.group(1).lower()
                        proxy_val = get_identity_locked_proxy(var)
                        if proxy_val is not None: missing_registry[var] = proxy_val
                    window_attempts += 1

        if not window_passed:
            print(f"❌ Structural fail at window {current_solve_start}.")
            sys.exit(1)
            
        # Increment to next step
        current_solve_start += 1 if current_solve_start == pd.Period('1989Q4', freq='Q') else step_size
            
    # 5. Final Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
    
    # Run final full-sample trace
    final_results = model.init_trac(first_actual, full_end, final_data, solver_params)
    final_results.to_csv(output_path)
    
    print(f"✅ Build Successful: Residuals archived at {output_path}")

if __name__ == "__main__":
    run_pro_engine()