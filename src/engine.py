import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #575)")
    
    working_dir = os.getcwd()
    # Path Discovery logic
    search_paths = [
        os.path.join(working_dir, "data/longdata.csv"),
        os.path.join(working_dir, "longdata.csv"),
        "/home/spark/data/longdata.csv"
    ]
    
    x_path = next((p for p in search_paths if os.path.exists(p)), None)
    processed_dir = os.path.join(working_dir, "data/processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load Y (Targets) first so we have a fallback
    y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    y_df = pd.concat([
        pd.read_csv(os.path.join(processed_dir, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 2. Load or Mock X (Backbone)
    if x_path:
        print(f"✅ Found backbone at: {x_path}")
        x_df = pd.read_csv(x_path)
        x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
    else:
        print("⚠️ longdata.csv NOT FOUND. Generating skeletal backbone from Y...")
        # We create a backbone of 1.0s for every variable in model.xml 
        # that isn't in your Y data to prevent 'missing variable' crashes.
        x_df = pd.DataFrame(1.0, index=y_df.index, columns=['upkbfir', 'dmptmax', 'pcap']) 
        # combine_first will merge your real Y data into this skeletal X
    
    # 3. Solve for e
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        results = model.init_trac(pd.Period("1989Q4", freq="Q"), y_df.index.max(), combined_df)
        results.to_csv(os.path.join(results_dir, "calibration_residuals_e.csv"))
        print(f"✅ SUCCESS: Build #575 finished.")
    except Exception as e:
        print(f"❌ Solver Error: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()