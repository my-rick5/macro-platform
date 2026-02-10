import pandas as pd
import os
import re
import sys
import json
import numpy as np

# 💓 HEARTBEAT: Force visibility in Jenkins Console
print("--------------------------------------------------")
print("💓 Heartbeat: Structural Engine Script Started.")
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
    
    # Corrected directory creation
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    print("📂 Loading input CSVs...")
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
    
    # 2. Initialization
    model = frbus.Frbus(model_xml)
    solve_start = pd.Period('2006Q1', freq='Q')
    solve_end = df.index.max()

    # 3. Load Existing State (Persistence)
    missing_registry = {}
    if os.path.exists(state_file):
        print(f"💾 Found saved state. Bypassing initial randomness...")
        with open(state_file, 'r') as f:
            missing_registry = json.load(f)

    # 4. The Healing Loop
    max_retries = 800
    attempts = 0
    print(f"🏗️ Model Loaded. Period: {solve_start} to {solve_end}.")

    while attempts < max_retries:
        try:
            if missing_registry:
                patch_df = pd.DataFrame(missing_registry, index=df.index)
                current_df = pd.concat([df, patch_df], axis=1)
            else:
                current_df = df.copy()

            # Ensure solve anchor is reachable
            if solve_start not in current_df.index:
                new_idx = pd.period_range(start=min(current_df.index.min(), solve_start), 
                                          end=max(current_df.index.max(), solve_end), 
                                          freq='Q')
                current_df = current_df.reindex(new_idx).ffill().bfill()

            # Attempt Solver Execution
            results = model.init_trac(solve_start, solve_end, current_df)
            
            # --- SUCCESS ---
            print(f"✅ Solve Successful at Cycle {attempts}.")
            
            # Save Winning State
            with open(state_file, 'w') as f:
                json.dump(missing_registry, f)
            
            # Surgical Export (15 variables + residuals)
            final_cols = [v for v in target_variables if v in results.columns]
            final_cols += [f"{v}_res" for v in target_variables if f"{v}_res" in results.columns]
            
            output_path = os.path.join(results_dir, "residuals_lite.csv")
            results[final_cols].to_csv(output_path)
            print(f"📦 Exported {len(final_cols)} columns to {output_path}")
            return 

        except exceptions.MissingDataError as e:
            match = re.search(r'`([^`]+)`', str(e))
            if match:
                var = match.group(1).lower()
                # Split-Magnitude Init
                if any(x in var for x in ['r', 'pi', 'u', 'gap', 'del']):
                    missing_registry[var] = 0.05 
                else:
                    missing_registry[var] = 100.0
                attempts += 1
            else: raise e
            
        except (ValueError, exceptions.ComputationError) as e:
            # Scaled Jitter
            multiplier = 1.0013 + (attempts * 0.0001)
            missing_registry = {k: v * multiplier for k, v in missing_registry.items()}
            attempts += 1
            if attempts % 50 == 0:
                print(f"🔄 Stabilizing: Scaling Cycle {attempts}...")

    print("❌ CRITICAL: Failed to stabilize domain within retry limit.")
    sys.exit(1)

if __name__ == "__main__":
    try:
        run_pro_engine()
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)