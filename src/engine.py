import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #625)")
    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    results_dir = os.path.join(working_dir, "results")
    
    # 1. Load Backbone (X)
    x_path = os.path.join(working_dir, "external_data/longdata.csv")
    x_df = pd.read_csv(x_path)
    x_df['date'] = pd.PeriodIndex(x_df['OBS' if 'OBS' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce').sort_index()
    x_df.columns = [c.lower() for c in x_df.columns]

    # 2. Load Targets (Y)
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    if not y_files:
        print("❌ FATAL: No processed Greenbook CSVs found."); sys.exit(1)
        
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 🕵️ DIAGNOSTIC: Check for actual overlap
    common_dates = x_df.index.intersection(y_df.index)
    print(f"🔍 Data Overlap: Found {len(common_dates)} quarters common to both Backbone and Targets.")
    if len(common_dates) < 4:
        print("🚨 ALERT: Insufficient data overlap. Solver will likely produce flat residuals.")

    # 3. Solve only for the Overlap Window
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    solve_start, solve_end = common_dates.min(), common_dates.max()
    print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
    
    try:
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # QUALITY CHECK: Fail if variation is non-existent
        for var in ['anngr', 'delrff']:
            if var in e_residuals.columns:
                v_score = e_residuals[var].std()
                print(f"Variable: {var} | Variance: {v_score:.5e}")
                if v_score < 1e-10:
                    print(f"❌ FATAL: {var} is flat. Check if input data for {var} is constant.")
                    sys.exit(1)

        e_residuals.to_csv(os.path.join(results_dir, "calibration_residuals_e.csv"))
        print("✅ SUCCESS: Calibration Complete.")
    except Exception as e:
        print(f"❌ Solver Crashed: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()