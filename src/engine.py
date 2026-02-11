import pandas as pd
import os
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Integrated Backbone Engine (Build #570)")
    
    # 1. Path Setup
    working_dir = os.getcwd()
    user_data_path = os.path.join(working_dir, "data/processed")
    # 🎯 UPDATED: Corrected filename to match your external_data folder
    external_data_path = os.path.join(working_dir, "external_data/longdata.csv") 
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 2. Load the FRB/US Backbone
    try:
        # Using read_csv since you confirmed it's a .csv file
        base_df = pd.read_csv(external_data_path)
        base_df['date'] = pd.PeriodIndex(base_df['date'], freq='Q')
        base_df = base_df.set_index('date')
        base_df.columns = [c.lower() for c in base_df.columns]
        print(f"📦 Loaded backbone: {len(base_df.columns)} variables from longdata.csv")
    except Exception as e:
        print(f"❌ FATAL: Could not load {external_data_path}: {e}")
        sys.exit(1)

    # 3. Load Your 15 Processed Variables
    files = [f for f in os.listdir(user_data_path) if f.endswith('.csv')]
    user_df = pd.concat([
        pd.read_csv(os.path.join(user_data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    user_df.columns = [c.lower() for c in user_df.columns]

    # 4. The Overlay (Build #410 Entropy Logic)
    # Merges your variables into the backbone so all 2000+ identities exist.
    combined_df = user_df.combine_first(base_df).sort_index()

    # 5. Solve & Calibrate
    from pyfrbus import frbus
    model = frbus.Frbus(os.path.join(working_dir, "models/model.xml"))
    solve_start, solve_end = pd.Period("1989Q4", freq="Q"), user_df.index.max()
    
    print(f"📈 Solving from {solve_start} using integrated backbone...")
    
    try:
        # Perform solve with tracking residuals enabled
        results = model.init_trac(solve_start, solve_end, combined_df)
        
        # Save Artifacts
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
        available = [v for v in lite_vars if v in results.columns]
        results[available].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
        
        print(f"✅ SUCCESS: Build #570 complete.")
    except Exception as e:
        print(f"❌ Solver Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()