import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #750 Path-Sync)")
    
    # PATH SYNC: These must match the directories created in your Dockerfile
    # We use 'external_data' for both because that is where we injected the baked CSVs
    working_dir = "/home/spark"
    proc_dir = "external_data" 
    ext_dir = "external_data"
    
    # 1. Load & Normalize Backbone
    longdata_path = os.path.join(working_dir, ext_dir, "longdata.csv")
    if not os.path.exists(longdata_path):
        print(f"❌ FATAL: Backbone file missing at {longdata_path}")
        sys.exit(1)

    x_df = pd.read_csv(longdata_path)
    x_df.columns = [c.lower() for c in x_df.columns]
    
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    
    # PERFORMANCE FIX: .copy() defragments the frame to stop the PerformanceWarning
    x_df = x_df.set_index('date').sort_index().copy()

    # 2. Load Processed Targets
    search_path = os.path.join(working_dir, proc_dir, "*.csv")
    y_files = glob.glob(search_path)
    
    # SAFETY CHECK: Filter out longdata.csv and check if any target CSVs exist
    target_files = [f for f in y_files if "longdata.csv" not in os.path.basename(f)]
    
    if not target_files:
        print(f"❌ FATAL: No target CSV files found in {os.path.join(working_dir, proc_dir)}")
        print(f"📂 Found in directory: {os.listdir(os.path.join(working_dir, proc_dir))}")
        raise ValueError("No objects to concatenate - verify Dockerfile COPY --from=dataprep step.")

    print(f"📊 Found {len(target_files)} target files. Starting concatenation...")
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in target_files
    ], axis=1).sort_index()
    
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. 🎯 PCE / DMPTMAX Hunter Logic
    pce_candidates = ['eco', 'ec', 'pce', 'pcec', 'ech']
    found_pce = next((c for c in pce_candidates if c in x_df.columns), None)

    if found_pce:
        print(f"✅ Found economic anchor: '{found_pce}'. Deriving dmptmax peak-tracker.")
        x_df['dmptmax'] = x_df[found_pce].cummax()
    else:
        print("⚠️ WARNING: No consumption series found. Using placeholder 100.0.")
        all_cols = sorted(x_df.columns.tolist())
        for i in range(0, len(all_cols), 6):
            print(f"  {', '.join(all_cols[i:i+6])}")
        y_df['dmptmax'] = 100.0 

    # 4. Solver Execution
    combined_df = y_df.combine_first(x_df).sort_index()
    common = x_df.index.intersection(y_df.index)
    
    if common.empty:
        print("❌ FATAL: No overlapping date range between backbone and targets.")
        sys.exit(1)
        
    start, end = common.min(), common.max()
    
    from pyfrbus import frbus
    model_path = os.path.join(working_dir, "models/model.xml")
    if not os.path.exists(model_path):
        print(f"❌ FATAL: Model file missing at {model_path}")
        sys.exit(1)
        
    model = frbus.Frbus(model_path)
    
    try:
        print(f"📈 Solving init_trac: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        
        results_dir = os.path.join(working_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported {len(e_residuals.loc[start:end])} quarters to {res_path}")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()