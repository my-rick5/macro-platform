import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Historical Truncation Mode)")
    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load Backbone X
    x_path = os.path.join(working_dir, "external_data/longdata.csv")
    x_df = pd.read_csv(x_path)
    x_df['date'] = pd.PeriodIndex(x_df['OBS' if 'OBS' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce').sort_index()
    x_df.columns = [c.lower() for c in x_df.columns]

    # 2. Load Targets Y
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. Define Window & Solve
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    common_dates = x_df.index.intersection(y_df.index)
    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # TRUNCATE: Remove steady-state noise outside of historical window
        e_residuals = e_residuals.loc[solve_start:solve_end]
        
        # 4. Final Export
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals)} quarters of historical residuals.")
        
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()