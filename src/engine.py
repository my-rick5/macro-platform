import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #657 Case-Normalization)")
    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    external_data_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone X
    x_path = os.path.join(external_data_dir, "longdata.csv")
    x_df = pd.read_csv(x_path)
    
    # Normalize headers to lowercase to prevent KeyError: 'date' vs 'DATE'
    x_df.columns = [c.lower() for c in x_df.columns]
    
    # Robust date column detection
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    if date_col not in x_df.columns:
        print(f"❌ FATAL: Date column missing. Found: {x_df.columns.tolist()}")
        sys.exit(1)
        
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Load Targets Y
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. Solver Requirement Injection (dmptmax)
    if 'dmptmax' not in y_df.columns and 'dmptmax' not in x_df.columns:
        print("🛠️ Injecting synthetic DMPTMAX to satisfy model structure.")
        y_df['dmptmax'] = 100.0 

    # 4. Final Merge & Solve
    combined_df = y_df.combine_first(x_df).sort_index()
    common_dates = x_df.index.intersection(y_df.index)
    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # Save results to the expected directory
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[solve_start:solve_end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals.loc[solve_start:solve_end])} quarters of residuals.")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()