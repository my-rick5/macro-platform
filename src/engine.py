import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #654 PCE Recovery)")

    working_dir = "/home/spark"
    processed_dir = os.path.join(working_dir, "data/processed")
    external_data_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone X
    x_path = os.path.join(external_data_dir, "longdata.csv")
    x_df = pd.read_csv(x_path)
    x_df['date'] = pd.PeriodIndex(x_df['OBS' if 'OBS' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()
    x_df.columns = [c.lower() for c in x_df.columns]

    # 2. Load Targets Y
    y_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. PCE / DMPTMAX RECOVERY LOGIC
    # Check if PCE exists under a different name in your backbone
    pce_synonyms = ['pce', 'pc', 'pcec', 'consumption']
    found_pce = next((s for s in pce_synonyms if s in x_df.columns), None)
    
    if found_pce:
        print(f"✅ Found PCE data in backbone column: '{found_pce}'. Mapping to model requirements.")
        # FRB/US derived variables often need the base series to be present
        if 'dmptmax' not in x_df.columns:
            # Simple approximation for DMPTMAX if the model just needs a placeholder
            # that scales with actual consumption
            x_df['dmptmax'] = x_df[found_pce].cummax()
    else:
        print("⚠️ WARNING: No PCE/Consumption data found in backbone!")
        print(f"📋 Available columns in longdata.csv: {x_df.columns.tolist()[:15]}...")

    # 4. Final Merge & Solve
    combined_df = y_df.combine_first(x_df).sort_index()
    common_dates = x_df.index.intersection(y_df.index)
    solve_start, solve_end = common_dates.min(), common_dates.max()
    
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    
    try:
        print(f"📈 Solving via init_trac: {solve_start} to {solve_end}")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[solve_start:solve_end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported residuals.")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()