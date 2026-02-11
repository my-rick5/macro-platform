import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #584)")
    
    working_dir = os.getcwd()
    # We define the expected paths but add a "Discovery" step
    data_dir = os.path.join(working_dir, "data")
    processed_dir = os.path.join(data_dir, "processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. 🎯 Recursive Backbone Discovery
    # This looks in /data, /source_code, and root for anything named longdata.csv
    search_locations = [
        os.path.join(data_dir, "longdata.csv"),
        os.path.join(working_dir, "longdata.csv"),
        "/source_code/data/longdata.csv",
        "/home/spark/data/longdata.csv"
    ]
    
    x_path = next((p for p in search_locations if os.path.exists(p)), None)
    
    if not x_path:
        print(f"❌ FATAL: longdata.csv not found.")
        print(f"Directory Scan: {os.listdir(data_dir) if os.path.exists(data_dir) else 'No Data Dir'}")
        sys.exit(1)

    # 2. Load Backbone (X)
    try:
        print(f"📦 Loading Backbone X from: {x_path}")
        x_df = pd.read_csv(x_path)
        date_col = 'OBS' if 'OBS' in x_df.columns else 'date'
        x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Backbone Load Error: {e}"); sys.exit(1)

    # 3. Load Targets (Y)
    try:
        y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
        print(f"📦 Merging {len(y_files)} Target variables...")
        y_df = pd.concat([
            pd.read_csv(os.path.join(processed_dir, f))
            .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
            .set_index('date') for f in y_files
        ], axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Target Load Error: {e}"); sys.exit(1)

    # 4. In-Memory Merge & Structural Solve
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    
    # Overlay Y (Targets) on top of X (Backbone)
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        print(f"📈 Solving Y = model(Beta, X) + e...")
        # Solve over the available target range
        e_residuals = model.init_trac(y_df.index.min(), y_df.index.max(), combined_df)
        
        # Save the result
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Build complete. Residuals saved to results/.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()