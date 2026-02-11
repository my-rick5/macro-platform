import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #577)")
    
    working_dir = os.getcwd()
    # 🎯 TARGETED SEARCH: We see a 'data' folder in your console output.
    # Let's look inside it.
    data_dir = os.path.join(working_dir, "data")
    x_path = os.path.join(data_dir, "longdata.csv")
    
    if not os.path.exists(x_path):
        # Check root as a backup
        x_path = os.path.join(working_dir, "longdata.csv")

    if not os.path.exists(x_path):
        print(f"❌ FATAL: longdata.csv not found in {working_dir} or {data_dir}")
        print(f"Data Dir Contents: {os.listdir(data_dir) if os.path.exists(data_dir) else 'N/A'}")
        sys.exit(1)

    print(f"✅ Backbone Found: {x_path}")
    
    # 1. Load X (Backbone)
    x_df = pd.read_csv(x_path).apply(pd.to_numeric, errors='coerce')
    x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
    x_df = x_df.set_index('date')
    x_df.columns = [c.lower() for c in x_df.columns]

    # 2. Load Y (Targets)
    processed_dir = os.path.join(data_dir, "processed")
    y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    y_df = pd.concat([
        pd.read_csv(os.path.join(processed_dir, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. Solve Y = model(Beta, X) + e
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        # Solving for residuals 'e'
        res = model.init_trac(pd.Period("1989Q4", freq="Q"), y_df.index.max(), combined_df)
        res.to_csv(os.path.join(working_dir, "results/calibration_residuals_e.csv"))
        print(f"✅ SUCCESS: Build #577 complete.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()