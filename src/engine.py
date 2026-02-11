import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #659 Economic Hunter)")
    working_dir, proc_dir, ext_dir = "/home/spark", "data/processed", "external_data"
    
    # 1. Load & Normalize Backbone
    x_df = pd.read_csv(os.path.join(working_dir, ext_dir, "longdata.csv"))
    x_df.columns = [c.lower() for c in x_df.columns]
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Load Processed Targets
    y_files = glob.glob(os.path.join(working_dir, proc_dir, "*.csv"))
    y_df = pd.concat([pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
                      for f in y_files], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. 🎯 PCE / DMPTMAX Hunter Logic
    # We hunt for standard FRB/US consumption codes: ECO (Expenditures), EC, or PCE
    pce_candidates = ['eco', 'ec', 'pce', 'pcec', 'ech']
    found_pce = next((c for c in pce_candidates if c in x_df.columns), None)

    if found_pce:
        print(f"✅ Found economic anchor: '{found_pce}'. Deriving dmptmax peak-tracker.")
        x_df['dmptmax'] = x_df[found_pce].cummax()
    else:
        print("⚠️ WARNING: No consumption series found. Using placeholder 100.0.")
        print("📋 Available columns in backbone (Search for your PCE variable here):")
        all_cols = sorted(x_df.columns.tolist())
        for i in range(0, len(all_cols), 6):
            print(f"  {', '.join(all_cols[i:i+6])}")
        y_df['dmptmax'] = 100.0 

    # 4. Solver Execution
    combined_df = y_df.combine_first(x_df).sort_index()
    common = x_df.index.intersection(y_df.index)
    start, end = common.min(), common.max()
    
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    
    try:
        print(f"📈 Solving init_trac: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals.loc[start:end])} quarters.")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()