import pandas as pd
import os
import re
import sys
import json
import numpy as np

print("--------------------------------------------------")
print("💓 Heartbeat: Auto-Scaling Window Engine Started.")
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
    state_file = "/home/spark/models/solver_state.json"
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

    # 🎯 2. NEW: UNIT ALIGNMENT PRE-CHECK
    # Detects if variables like HSTART are in units/millions vs billions
    print("⚖️ Normalizing units for structural consistency...")
    for col in df.columns:
        avg_val = df[col].mean()
        # Scale up if it's a 'Level' variable that is suspiciously small (< 10)
        is_rate = any(x in col for x in ['r', 'pi', 'u', 'gap', 'del'])
        if avg_val < 10 and not is_rate:
            print(f"  ⚠️ Auto-scaling {col}: {avg_val:.2f} -> {avg_val * 1000:.2f}")
            df[col] = df[col] * 1000
    
    # 3. Initialization
    model = frbus.Frbus(model_xml)
    full_start = pd.Period('2006Q1', freq='Q')
    full_end = df.index.max()

    # 4. Recursive Windowing Logic
    missing_registry = {}
    current_solve_start = full_start
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            missing_registry = json.load(f)
        print("💾 Loaded cached state as anchor.")

    while current_solve_start <= full_end:
        current_solve_end = min(current_solve_start + 3, full_end)
        print(f"🕒 Window: {current_solve_start} to {current_solve_end}")
        
        window_attempts = 0
        window_passed = False
        
        while window_attempts < 150:
            try:
                patch_df = pd.DataFrame(missing_registry, index=df.index)
                current_df = pd.concat([df, patch_df], axis=1)
                
                # Check for solve anchor
                if current_solve_start not in current_df.index:
                    new_idx = pd.period_range(start=min(current_df.index.min(), current_solve_start), 
                                              end=max(current_df.index.max(), full_end), freq='Q')
                    current_df = current_df.reindex(new_idx).ffill().bfill()

                # Solve window
                results = model.init_trac(current_solve_start, current_solve_end, current_df)
                
                # Update registry with final period values of the window
                for col in results.columns:
                    if col not in target_variables:
                        missing_registry[col] = float(results[col].iloc[-1])
                
                window_passed = True
                break
                
            except exceptions.MissingDataError as e:
                match = re.search(r'`([^`]+)`', str(e))
                if match:
                    var = match.group(1).lower()
                    # Smart Start: Rates small, Levels anchored to scaled data avg
                    missing_registry[var] = 0.05 if any(x in var for x in ['r','pi','u']) else 1000.0
                window_attempts += 1
            except (ValueError, exceptions.ComputationError):
                # Oscillation Jitter to break singularities
                jitter = 1.0 + (np.sin(window_attempts) * 0.02)
                missing_registry = {k: v * jitter for k, v in missing_registry.items()}
                window_attempts += 1

        if not window_passed:
            print(f"❌ Structural fail at window {current_solve_start}. Limit reached.")
            sys.exit(1)
        
        current_solve_start += 4
            
    # 5. Final Full Solve & Surgical Export
    print("🔥 Executing final full-period residuals calculation...")
    patch_df = pd.DataFrame(missing_registry, index=df.index)
    results = model.init_trac(full_start, full_end, pd.concat([df, patch_df], axis=1))
    
    with open(state_file, 'w') as f:
        json.dump(missing_registry, f)

    final_cols = [v for v in target_variables if v in results.columns]
    final_cols += [f"{v}_res" for v in target_variables if f"{v}_res" in results.columns]
    results[final_cols].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
    print("✅ Build Successful. Residuals saved.")

if __name__ == "__main__":
    try:
        run_pro_engine()
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)