import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #646 Overlap Check)")

    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    external_data_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone X (Historical baseline)
    x_path = os.path.join(external_data_dir, "longdata.csv")
    if not os.path.exists(x_path):
        print("❌ FATAL: longdata.csv is missing."); sys.exit(1)
        
    x_df = pd.read_csv(x_path)
    x_df['date'] = pd.PeriodIndex(x_df['OBS' if 'OBS' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Load Targets Y (Processed Excel sheets)
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    if not y_files:
        print("❌ FATAL: No target files found in data/processed."); sys.exit(1)

    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()

    # 3. Overlap Diagnostic & Protection
    print("-" * 40)
    if y_df.empty:
        print("❌ FATAL: Target DataFrame is EMPTY.")
        sys.exit(1)

    print(f"🕵️ SAMPLE TARGET DATES:   {y_df.index.tolist()[:2]}")
    print(f"🕵️ SAMPLE BACKBONE DATES: {x_df.index.tolist()[:2]}")
    
    common_dates = x_df.index.intersection(y_df.index)
    
    if common_dates.empty:
        # Range check to help debug century/format mismatches
        y_range = f"{y_df.index.year.min()} to {y_df.index.year.max()}"
        x_range = f"{x_df.index.year.min()} to {x_df.index.year.max()}"
        print(f"🕵️ Target Range:   {y_range}")
        print(f"🕵️ Backbone Range: {x_range}")
        print("-" * 40)
        print("❌ FATAL: No date overlap between Backbone and Targets."); sys.exit(1)
    
    print(f"✅ FOUND OVERLAP: {len(common_dates)} quarters.")
    print("-" * 40)

    # 4. Model Solving Stage
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        e_residuals = e_residuals.loc[solve_start:solve_end] # Historical Truncation
        
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals)} residuals.")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()