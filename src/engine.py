import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Historical Truncation Mode)")

    # 1. Environment & Path Setup
    working_dir = "/home/spark"
    external_data_dir = os.path.join(working_dir, "external_data")
    processed_dir = os.path.join(working_dir, "data/processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 2. Load Backbone X (longdata.csv)
    x_path = os.path.join(external_data_dir, "longdata.csv")
    if not os.path.exists(x_path):
        fallback = glob.glob(os.path.join(working_dir, "**/longdata.csv"), recursive=True)
        x_path = fallback[0] if fallback else None

    if not x_path:
        print("❌ FATAL: longdata.csv is missing."); sys.exit(1)

    # 3. Load & Clean Backbone X
    try:
        x_df = pd.read_csv(x_path)
        date_col = 'OBS' if 'OBS' in x_df.columns else 'date'
        x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce').sort_index()
        x_df.columns = [c.lower() for c in x_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Failed to parse Backbone X: {e}"); sys.exit(1)

    # 4. Load Greenbook Targets Y
    try:
        y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
        if not y_files:
            print("❌ FATAL: No target files found."); sys.exit(1)
            
        y_df = pd.concat([
            pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
            for f in y_files
        ], axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Failed to merge Target Y files: {e}"); sys.exit(1)

    # 5. Define Historical Window & Solve
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    # Lock solve to the actual historical data overlap
    common_dates = x_df.index.intersection(y_df.index)
    if common_dates.empty:
        print("❌ FATAL: No overlapping dates found between Backbone and Targets."); sys.exit(1)

    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # 🛡️ TRUNCATION: Delete rows outside the historical window to remove steady-state noise
        e_residuals = e_residuals.loc[solve_start:solve_end]
        
        # 6. Sanity Quality Check
        for var in ['anngr', 'delrff']:
            if var in e_residuals.columns:
                std_val = e_residuals[var].std()
                print(f"Variable: {var.ljust(10)} | StdDev: {std_val:.6e}")
                if std_val < 1e-10:
                    print(f"🚨 FATAL: {var} is flat. Historical calibration failed.")
                    sys.exit(1)

        # 7. Export Results
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals)} quarters of historical residuals.")
        
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()