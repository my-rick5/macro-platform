import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    # Header updated to verify you are running the right version
    print("🚀 Heartbeat: Full Calibration Engine (Build #645 Overlap Diagnostic)")

    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    external_data_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone X
    x_path = os.path.join(external_data_dir, "longdata.csv")
    x_df = pd.read_csv(x_path)
    x_df['date'] = pd.PeriodIndex(x_df['OBS' if 'OBS' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Load Targets Y
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()

    # 3. CRITICAL DIAGNOSTIC: Why is there no overlap?
    print("-" * 40)
    print(f"🕵️ RAW TARGET SAMPLE: {y_df.index[:2].tolist()}")
    print(f"🕵️ RAW BACKBONE SAMPLE: {x_df.index[:2].tolist()}")
    
    common_dates = x_df.index.intersection(y_df.index)
    
    if common_dates.empty:
        y_years = sorted(list(set(d.year for d in y_df.index)))
        x_years = sorted(list(set(d.year for d in x_df.index)))
        print(f"🕵️ Target Year Range:   {y_years[0]} to {y_years[-1]}")
        print(f"🕵️ Backbone Year Range: {x_years[0]} to {x_years[-1]}")
        print("-" * 40)
        print("❌ FATAL: No date overlap between Backbone and Targets."); sys.exit(1)
    
    print(f"✅ FOUND OVERLAP: {len(common_dates)} quarters.")
    print("-" * 40)

    # 4. Solve
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    e_residuals = model.init_trac(solve_start, solve_end, combined_df)
    e_residuals = e_residuals.loc[solve_start:solve_end]
    
    res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
    e_residuals.to_csv(res_path)
    print(f"✅ SUCCESS: Exported {len(e_residuals)} historical residuals.")

if __name__ == "__main__":
    run_pro_engine()