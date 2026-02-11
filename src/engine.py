import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #573)")
    
    # 1. Paths
    working_dir = os.getcwd()
    data_dir = os.path.join(working_dir, "data")
    processed_dir = os.path.join(data_dir, "processed")
    results_dir = os.path.join(working_dir, "results")
    
    # 2. Load X (Backbone from longdata.csv)
    # This is the X in your equation
    try:
        x_df = pd.read_csv(os.path.join(data_dir, "longdata.csv"))
        x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
    except Exception as e:
        print(f"❌ FATAL: X (longdata) failed to load: {e}"); sys.exit(1)

    # 3. Load Y (Targets from GBweb CSVs)
    # This is the Y in your equation
    y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
    y_df = pd.concat([
        pd.read_csv(os.path.join(processed_dir, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in y_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 4. Map X + Y
    # combined_df ensures the model has the full backbone but hits your targets
    combined_df = y_df.combine_first(x_df).sort_index()

    # 5. Solve for e (Residuals)
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    solve_start, solve_end = pd.Period("1989Q4", freq="Q"), y_df.index.max()
    
    try:
        # This calculates e = Y - model(Beta, X)
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # Save e (The error/add-factors)
        e_residuals.to_csv(os.path.join(results_dir, "calibration_residuals_e.csv"))
        
        # Save a "Lite" version of the targets for verification
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in e_residuals.columns]
        e_residuals[available].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
        
        print(f"✅ SUCCESS: Build #573 complete. 'e' saved to results/.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()