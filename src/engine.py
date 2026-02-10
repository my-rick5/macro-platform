import pandas as pd
import os
import re
import sys
import json
import numpy as np

print("--------------------------------------------------")
print("💓 Heartbeat: Robust-Momentum Engine Started.")
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
    if not files: return
        
    df_raw = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') 
        for f in files
    ], axis=1).sort_index()
    
    df_raw.index = pd.PeriodIndex(df_raw.index, freq='Q')
    df_raw.columns = [c.lower() for c in df_raw.columns]
    target_variables = list(df_raw.columns)

    # 🎯 2. ROBUST DYNAMIC BUFFER (Anti-Infinity)
    first_actual = df_raw.index.min()
    buffer_idx = pd.period_range(start=first_actual - 4, end=first_actual - 1, freq='Q')
    
    # FIX: Calculate momentum while handling Inf/NaN spikes
    growth_series = df_raw.select_dtypes(include=[np.number]).pct_change()
    avg_growth = growth_series.replace([np.inf, -np.inf], np.nan).mean().mean()
    
    # Clip to +/- 5% to prevent extreme structural shocks
    avg_growth = np.clip(avg_growth, -0.05, 0.05)
    if np.isnan(avg_growth): avg_growth = 0.005 
    
    print(f"📊 Data start: {first_actual}. Seeding momentum at {avg_growth:.4f} (Clipped)")
    
    buffer_df = pd.DataFrame(index=buffer_idx, columns=df_raw.columns)
    for col in df_raw.columns:
        if any(x in col for x in ['g', 'pi', 'r', 'u', 'gap']):
            buffer_df[col] = avg_growth 
        else:
            buffer_df[col] = df_raw[col].iloc[0]
    
    df = pd.concat([buffer_df, df_raw]).sort_index()

    # 3. UNIT & ACCOUNTING ENFORCEMENT
    print("⚖️ Normalizing units and enforcing accounting identities...")
    for col in df.columns:
        avg_val = df[col].mean()
        is_rate = any(x in col for x in ['r', 'pi', 'u', 'gap', 'del'])
        if avg_val < 10 and not is_rate:
            df[col] = df[col] * 1000

    if all(x in df.columns for x in ['gngdp', 'gppce', 'gip']):
        df['gnx'] = df['gngdp'] - (df['gppce'] + df['gip'])

    if all(x in df.columns for x in ['gngdp', 'grgdp', 'gpgdp']):
        df['gpgdp'] = df['gngdp'] - df['grgdp']
    
    # 4. Initialization
    model = frbus.Frbus(model_xml)
    solve_start = buffer_idx[0]
    full_end = df.index.max()

    # 5. Recursive Windowing Logic
    missing_registry = {}
    current_solve_start = solve_start
    
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

                results = model.init_trac(current_solve_start, current_solve_end, current_df)
                
                for col in results.columns:
                    if col not in target_variables:
                        missing_registry[col] = float(results[col].iloc[-1])
                
                window_passed = True
                break
                
            except exceptions.MissingDataError as e:
                match = re.search(r'`([^`]+)`', str(e))
                if match:
                    var = match.group(1).lower()
                    missing_registry[var] = 0.05 if any(x in var for x in ['r','pi','u']) else 1000.0
                window_attempts += 1
            except (ValueError, exceptions.ComputationError):
                jitter = 1.0 + (np.sin(window_attempts) * 0.02)
                missing_registry = {k: v * jitter for k, v in missing_registry.items()}
                window_attempts += 1

        if not window_passed:
            print(f"❌ Structural fail at window {current_solve_start}.")
            sys.exit(1)
        
        current_solve_start += 4
            
    # 6. Final Solve & Export
    print(f"🔥 Finalizing residuals for {first_actual} through {full_end}...")
    patch_df = pd.DataFrame(missing_registry, index=df.index)
    results = model.init_trac(first_actual, full_end, pd.concat([df, patch_df], axis=1))
    
    final_cols = [v for v in target_variables if v in results.columns]
    final_cols += [f"{v}_res" for v in target_variables if f"{v}_res" in results.columns]
    results[final_cols].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
    print("✅ Build Successful. Residuals exported.")

if __name__ == "__main__":
    try:
        run_pro_engine()
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        sys.exit(1)