import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #641 Recovery)")

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

    try:
        x_df = pd.read_csv(x_path)
        date_col = 'OBS' if 'OBS' in x_df.columns else 'date'
        x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce').sort_index()
        x_df.columns = [c.lower() for c in x_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Failed to parse Backbone X: {e}"); sys.exit(1)

    # 3. Load Greenbook Targets Y (With Protection against Empty Directory)
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    
    if not y_files:
        print("\n" + "!"*50)
        print("❌ FATAL: No target files found in data/processed!")
        print("This means preprocess.py did not find any matching sheets in library.xlsx.")
        print("Check your sheet name mapping in preprocess.py.")
        print("!"*50 + "\n")
        sys.exit(1)
            
    try:
        y_df = pd.concat([
            pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
            for f in y_files
        ], axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
        print(f"📦 Successfully merged {len(y_files)} target files.")
    except Exception as e:
        print(f"❌ FATAL: Failed to merge Target Y files: {e}"); sys.exit(1)

    # 4. Define Historical Window & Solve
    from pyfrbus import frbus
    model_path = os.path.join(working_dir, "models/model.xml")
    model = frbus.Frbus(model_path)
    combined_df = y_df.combine_first(x_df).sort_index()
    
    # Identify the overlapping historical window
    common_dates = x_df.index.intersection(y_df.index)
    if common_dates.empty:
        print("❌ FATAL: No date overlap between Backbone and Targets."); sys.exit(1)

    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # 🛡️ TRUNCATION: Keep only the historical solve to avoid steady-state noise
        e_residuals = e_residuals.loc[solve_start:solve_end]
        
        # 5. Export Results
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals)} quarters of historical residuals.")
        
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()