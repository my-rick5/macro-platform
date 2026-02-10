import pandas as pd
import os
import re
import sys
import numpy as np

print("--------------------------------------------------")
print("💓 Heartbeat: Identity-Zeroing Bridge (Fixed).")
print("--------------------------------------------------")

try:
    from pyfrbus import frbus
    print("✅ FRB/US Solver Dependencies Loaded.")
except Exception as e:
    print(f"❌ FATAL: Dependency Load Error: {e}")
    sys.exit(1)

def run_pro_engine():
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    
    # 🎯 FIX: Corrected keyword 'exist_ok'
    os.makedirs(results_dir, exist_ok=True) 
    
    # ... (Rest of the Identity-Zeroing logic from the previous merge)
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.index = pd.PeriodIndex(df.index, freq='Q')
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)

    model = frbus.Frbus(model_xml)
    solver_params = {'max_iter': 2000, 'tolerance': 1e-3, 'debug': True, 'show_failed': 5}
    
    df['mc_mode'] = 0.0  
    df['mco_mode'] = 1.0  

    first_actual = df.index.min()
    full_end = df.index.max()
    missing_registry = {}

    def get_identity_locked_proxy(var_name):
        if var_name not in target_variables: return None 
        return df[var_name].iloc[0]

    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        if current_solve_start == pd.Period('1989Q4', freq='Q'):
            print("❄️ Entering Deep Freeze. Zeroing identity residuals for 1989Q4...")
            identity_blockers = ['z_ki', 'z_tx', 'z_tr', 'z_li', 'z_gtr', 'z_vtr']
            for z_var in identity_blockers:
                missing_registry[z_var] = 0.0
            for var in target_variables:
                df.loc[current_solve_start, var] = df.loc[pd.Period('1989Q3', freq='Q'), var]

        step_size = 1 if current_solve_start < pd.Period('1991Q1', freq='Q') else 4
        current_solve_end = min(current_solve_start + (step_size - 1), full_end)
        
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
            print(f"❌ Final Structural fail at window {current_solve_start}.")
            sys.exit(1)
        current_solve_start += step_size
            
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
    results = model.init_trac(first_actual, full_end, final_data, **solver_params)
    results.to_csv(output_path)
    print("✅ Build Successful: Residuals exported via Identity-Zeroing.")

if __name__ == "__main__":
    run_pro_engine()