import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #576)")
    
    working_dir = os.getcwd()
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 1. 🎯 ROBUST FILE DISCOVERY
    # We are searching everywhere because Docker mounts can be tricky
    possible_locations = [
        os.path.join(working_dir, "data/longdata.csv"),
        os.path.join(working_dir, "longdata.csv"),
        "/home/spark/data/longdata.csv",
        "/home/spark/longdata.csv"
    ]
    
    x_path = next((p for p in possible_locations if os.path.exists(p)), None)
    
    if not x_path:
        print("❌ FATAL: longdata.csv is missing from the container.")
        print(f"Current Directory: {working_dir} | Contents: {os.listdir(working_dir)}")
        sys.exit(1)

    # 2. Load X (Backbone)
    print(f"✅ Backbone Found: {x_path}")
    x_df = pd.read_csv(x_path).apply(pd.to_numeric, errors='coerce')
    x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
    x_df = x_df.set_index('date')
    x_df.columns = [c.lower() for c in x_df.columns]

    # 3. Load Y (Targets from Processed Folder)
    processed_dir = os.path.join(working_dir, "data/processed")
    y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    y_df = pd.concat([
        pd.read_csv(os.path.join(processed_dir, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 4. The Equation: Y = model(Beta, X) + e
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        # Solving for 'e' (Residuals)
        solve_start = pd.Period("1989Q4", freq="Q")
        e_residuals = model.init_trac(solve_start, y_df.index.max(), combined_df)
        
        e_residuals.to_csv(os.path.join(results_dir, "calibration_residuals_e.csv"))
        print(f"✅ SUCCESS: Residuals calculated. {len(e_residuals)} rows exported.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()