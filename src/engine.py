import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #579)")
    
    working_dir = os.getcwd()
    data_dir = os.path.join(working_dir, "data")
    
    # 1. 🎯 Aggressive Discovery
    # Look for anything that looks like our backbone in root or data/
    search_pattern = ["data/*long*", "*long*", "data/*.csv", "data/*.TXT"]
    found_files = []
    for pattern in search_pattern:
        found_files.extend(glob.glob(os.path.join(working_dir, pattern)))
    
    # Filter out directories and the processed folder
    x_files = [f for f in found_files if os.path.isfile(f) and "processed" not in f]
    
    if not x_files:
        print(f"❌ FATAL: No backbone file found.")
        print(f"Contents of /data: {os.listdir(data_dir)}")
        print(f"Contents of root: {os.listdir(working_dir)}")
        sys.exit(1)
        
    x_path = x_files[0]
    print(f"✅ Backbone Found: {os.path.basename(x_path)}")

    # 2. Load X (Backbone)
    x_df = pd.read_csv(x_path).apply(pd.to_numeric, errors='coerce')
    x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
    x_df = x_df.set_index('date')
    x_df.columns = [c.lower() for c in x_df.columns]

    # 3. Load Y (Targets)
    processed_dir = os.path.join(data_dir, "processed")
    y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    y_df = pd.concat([
        pd.read_csv(os.path.join(processed_dir, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 4. Solve for e
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        res = model.init_trac(pd.Period("1989Q4", freq="Q"), y_df.index.max(), combined_df)
        res.to_csv(os.path.join(working_dir, "results/calibration_residuals_e.csv"))
        print(f"✅ SUCCESS: Build #579 complete.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()