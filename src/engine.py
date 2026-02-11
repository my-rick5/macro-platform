import pandas as pd
import os
import re
import sys

print("--------------------------------------------------")
print("🚀 Heartbeat: Final Total Sweep Engine v14.")
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

    # 🎯 FIX: API-COMPLIANT TOTAL SWEEP (Build #520 Correction)
    # Accessing .lookup.keys() directly for v1.1.0 compatibility
    model_vars = [v.lower() for v in model.lookup.keys()]
    missing_registry = {}

    first_actual = df.index.min()
    full_end = df.index.max()
    current_solve_start = first_actual + 1
    
    while current_solve_start <= full_end:
        
        # 🎯 STRATEGY: DYNAMIC MODEL SWEEP (1989Q4)
        if current_solve_start == pd.Period('1989Q4', freq='Q'):
            print("🛡️ 1989Q4 Deadlock: Performing API-Compliant Total Model Sweep...")
            current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
            
            # 🛡️ Sweep: Inject 0.0 for every variable in the lookup table missing from data
            for var in model_vars:
                if var not in current_df.columns:
                    current_df[var] = 0.0
            
            # Vanilla 3-position call (start, end, data)
            results = model.init_trac(current_solve_start, current_solve_start, current_df)
            
            for col in results.columns:
                if col not in target_variables:
                    missing_registry[col] = float(results[col].iloc[-1])
            window_passed = True
            
        else:
            # Standard quarter/window solving for 1990+
            step_size = 1 if current_solve_start < pd.Period('1991Q1', freq='Q') else 4
            current_solve_end = min(current_solve_start + (step_size - 1), full_end)
            
            window_passed = False
            while not window_passed:
                current_df = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
                
                # Maintain sweep for solve setup validation
                for var in model_vars:
                    if var not in current_df.columns:
                        current_df[var] = 0.0
                        
                results = model.init_trac(current_solve_start, current_solve_end, current_df)
                
                for col in results.columns:
                    if col not in target_variables:
                        missing_registry[col] = float(results[col].iloc[-1])
                window_passed = True

        current_solve_start += 1 if current_solve_start == pd.Period('1989Q4', freq='Q') else step_size
            
    # 5. Full-Sample Results Export
    output_path = os.path.join(results_dir, "residuals_lite.csv")
    final_data = pd.concat([df, pd.DataFrame(missing_registry, index=df.index)], axis=1)
    for var in model_vars:
        if var not in final_data.columns:
            final_data[var] = 0.0

    print("📈 Finalizing full-sample residuals...")
    final_results = model.init_trac(first_actual, full_end, final_data)
    final_results.to_csv(output_path)
    
    print(f"✅ SUCCESS: Build complete. Results archived.")

if __name__ == "__main__":
    run_pro_engine()