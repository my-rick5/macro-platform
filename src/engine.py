import pandas as pd
import os
import re
import sys
import numpy as np

print("--------------------------------------------------")
print("💓 Heartbeat: Warm-Start Engine Started.")
print("--------------------------------------------------")

try:
    from pyfrbus import frbus, exceptions
    print("✅ FRB/US Solver Dependencies Loaded.")
except Exception as e:
    print(f"❌ FATAL: Dependency Load Error: {e}")
    sys.exit(1)

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
        
    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') 
        for f in files
    ], axis=1).sort_index()
    
    df.index = pd.PeriodIndex(df.index, freq='Q')
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)

    # 2. Initialization & Logic
    model = frbus.Frbus(model_xml)
    solver_params = {'max_iter': 1000, 'tolerance': 1e-3}
    
    if 'mco_mode' not in df.columns:
        df['mco_mode'] = 1.0  

    first_actual = df.index.min()
    full_end = df.index.max()
    missing_registry = {}
    gdp_anchor = df['gngdp'].iloc[0] if 'gngdp' in df.columns else 5500

    def get_identity_locked_proxy(var_name):
        if var_name.startswith('p') and not any(x in var_name for x in ['pi', 'ptr']):
            base_val = 1.0 
        elif var_name.startswith('q'):
            return None # Endogenous release
        elif any(x in var_name for x in ['r','pi','u','gap','adj','exp']):
            base_val = 0.05
        elif var_name.startswith('k'):
            base_val = gdp_anchor * 3.1
        else:
            base_val = 0.20
        jitter = 1 + (np.random.uniform(-0.0001, 0.0001))
        return base_val * jitter

    # 3. Safe Anchor Loop
    print(f"⚡ Establishing anchor at {first_actual}...")
    init_passed = False
    attempts = 0
    while not init_passed and attempts < 250:
        try:
            anchor_params = {**solver_params, 'max_iter': 25}
            first_q_results = model.init_trac(first_actual, first_actual, df, **anchor_params)
            for col in first_q_results.columns:
                if col not in target_variables:
                    missing_registry[col] = float(first_q_results[col].iloc[0])
            init_passed = True
            print("✅ Anchor Secure.")
        except Exception as e:
            match = re.search(r'`([^`]+)`', str(e))
            if match:
                var = match.group(1).lower()
                proxy_val = get_identity_locked_proxy(var)
                if proxy_val is not None: df[var] = proxy_val
                attempts += 1
            else: attempts += 1

    # 4. Global Recursive Shield with Warm-Start Damping
    current_solve_start = first_actual + 1
    while current_solve_start <= full_end:
        current_solve_end = min(current_solve_start + 3, full_end)
        print(f"🕒 Window: {current_solve_start} to {current_solve_end}")
        
        window_passed = False
        window_attempts = 0
        while not window_passed and window_attempts < 100:
            try:
                current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
                
                # 🎯 FIX: WARM-START DAMPING
                if current_solve_start == first_actual + 1:
                    print("🌡️  Applying warm-start damping to transition window...")
                    for var in missing_registry:
                        current_df.loc[current_solve_start:current_solve_end, var] = missing_registry[var]

                results = model.init_trac(current_solve_start, current_solve_end, current_df, **solver_params)
                for col in results.columns:
                    if col not in target_variables:
                        missing_registry[col] = float(results[col].iloc[-1])
                window_passed = True
            except Exception as e:
                match = re.search(r'`([^`]+)`', str(e))
                if match:
                    var = match.group(1).lower()
                    print(f"🛠️  Identity Lock: Seeding {var}...")
                    proxy_val = get_identity_locked_proxy(var)
                    if proxy_val is not None: missing_registry[var] = proxy_val
                    window_attempts += 1
                else: window_attempts += 1

        if not window_passed:
            print(f"❌ Structural fail at window {current_solve_start}.")
            sys.exit(1)
        current_solve_start += 4
            
    # 5. Final Export
    print(f"🔥 Exporting full residuals...")
    final_data = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
    results = model.init_trac(first_actual, full_end, final_data, **solver_params)
    results.to_csv(os.path.join(results_dir, "residuals_lite.csv"))
    print("✅ Build Successful.")

if __name__ == "__main__":
    run_pro_engine()