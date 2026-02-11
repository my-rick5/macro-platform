import pandas as pd
import os
import sys

def run_pro_engine():
    # Identifies the build in the Jenkins Console
    print("🚀 Heartbeat: Calibration Engine (Build #574)")
    
    # 1. Dynamic Path Setup
    working_dir = os.getcwd()
    # This points to the 'data' folder relative to where engine.py is running
    data_dir = os.path.join(working_dir, "data")
    processed_dir = os.path.join(data_dir, "processed")
    results_dir = os.path.join(working_dir, "results")
    
    # Ensure results directory exists for the 'e' residuals
    os.makedirs(results_dir, exist_ok=True)
    
    # 2. Load X (Backbone: longdata.csv)
    # This provides the historical context for the Beta coefficients
    x_path = os.path.join(data_dir, "longdata.csv")
    if not os.path.exists(x_path):
        print(f"❌ FATAL: {x_path} not found. Current Dir: {working_dir}")
        print(f"Directory contents: {os.listdir(data_dir)}")
        sys.exit(1)

    try:
        x_df = pd.read_csv(x_path)
        x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
        print(f"✅ Backbone X loaded: {len(x_df.columns)} variables.")
    except Exception as e:
        print(f"❌ FATAL: X failed to load: {e}"); sys.exit(1)

    # 3. Load Y (Targets: Greenbook files)
    # These are the Y values in your Y = model(Beta, X) + e equation
    try:
        y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
        y_df = pd.concat([
            pd.read_csv(os.path.join(processed_dir, f))
            .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
            .set_index('date') for f in y_files
        ], axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
        print(f"✅ Targets Y loaded: {len(y_df.columns)} variables.")
    except Exception as e:
        print(f"❌ FATAL: Y failed to load: {e}"); sys.exit(1)

    # 4. Solve for e (Residuals)
    # This is where the structural model from model.xml (Beta) is applied
    from pyfrbus import frbus
    model_path = os.path.join(working_dir, "models/model.xml")
    model = frbus.Frbus(model_path)
    
    # Overlay Y onto X
    combined_df = y_df.combine_first(x_df).sort_index()
    
    solve_start = pd.Period("1989Q4", freq="Q")
    solve_end = y_df.index.max()
    
    try:
        # init_trac solves for the 'e' that makes the model hit the GB targets
        print(f"📈 Solving for residuals 'e' from {solve_start} to {solve_end}...")
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # Save the specific calibration error terms
        e_residuals.to_csv(os.path.join(results_dir, "calibration_residuals_e.csv"))
        print(f"✅ SUCCESS: Calibration complete. Residuals saved to results/.")
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()