import pandas as pd
import os
import re
import sys
import numpy as np

print("--------------------------------------------------")
print("💓 Heartbeat: Universal Release + Artifact Fix.")
print("--------------------------------------------------")

try:
    from pyfrbus import frbus, exceptions
    print("✅ FRB/US Solver Dependencies Loaded.")
except Exception as e:
    print(f"❌ FATAL: Dependency Load Error: {e}")
    sys.exit(1)

def run_pro_engine():
    # 🎯 FIX: Use relative paths for Jenkins Workspace visibility
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: 
        print("❌ No data files found.")
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

    # 2. Model Setup
    model = frbus.Frbus(model_xml)
    solver_params = {
        'max_iter': 1000, 
        'tolerance': 1e-3,
        'debug': True,
        'show_failed': 5,
        'log_level': 'INFO'
    }
    
    # Force Adaptive Expectations for the transition period
    df['mc_mode'] = 0.0  
    df['mco_mode'] = 1.0  

    first_actual = df.index.min()
    full_end = df.index.max()
    missing_registry = {}

    # 🎯 STRATEGY: UNIVERSAL ENDOGENOUS RELEASE
    def get_identity_locked_proxy(var_name):
        # Release ALL variables not in our core list to solve the 1989Q4 deadlock
        if var_name not in target_variables:
            return None 
            
        base_val = df[var_name].iloc[0] if var_name in df.columns else 0.20
        jitter = 1 + (np.random.uniform(-0.0001, 0.0001))
        return base_val * jitter

    # 3. Recursive solve with Temporal Compression
    print(f"⚡ Establishing universal anchor at {first_actual}...")
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        # Step quarter-by-quarter through the 1990 danger zone
        step_size = 1 if current_solve_start < pd.Period('1991Q1', freq='Q') else 4
        current_solve_end = min(current_solve_start + (step_size - 1), full_end)
        print(f"🕒 Solving Window: {current_solve_start} to {current_solve_end}")
        
        window_passed = False
        window_attempts = 0
        while not window_passed and window_attempts < 100:
            try:
                current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
                results = model.init_trac(current_solve_start, current_solve_end, current_df, **solver_params)
                
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
            print(f"❌ Failed to solve window at {current_solve_start}")
            sys.exit(1)
            
        current_solve_start += step_size
            
    # 4. Final Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    print(f"🔥 Final solve complete. Exporting to: {output_path}")
    
    final_data = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
    results = model.init_trac(first_actual, full_end, final_data, **solver_params)
    results.to_csv(output_path)
    
    print("✅ Build Successful: Artifacts ready for Jenkins archiving.")

if __name__ == "__main__":
    run_pro_engine()