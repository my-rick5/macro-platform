import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #586)")
    
    # 1. Path Configuration
    working_dir = os.getcwd()
    # We prioritize your external_data folder as the primary X source
    external_data_dir = os.path.join(working_dir, "external_data")
    processed_dir = os.path.join(working_dir, "data/processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 2. 🔍 Locate Backbone X (longdata.csv)
    x_path = os.path.join(external_data_dir, "longdata.csv")
    
    if not os.path.exists(x_path):
        print(f"⚠️ Warning: longdata.csv not found in {external_data_dir}")
        print("🔍 Searching all directories for fallback...")
        fallback_search = glob.glob(os.path.join(working_dir, "**/longdata.csv"), recursive=True)
        if fallback_search:
            x_path = fallback_search[0]
            print(f"✅ Found backbone at fallback location: {x_path}")
        else:
            print(f"❌ FATAL: longdata.csv is completely missing from the container.")
            print(f"Current Dir Contents: {os.listdir(working_dir)}")
            sys.exit(1)

    # 3. Load Backbone X
    try:
        x_df = pd.read_csv(x_path)
        # Handle different date column names (OBS vs date)
        date_col = 'OBS' if 'OBS' in x_df.columns else 'date'
        x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
        print(f"📦 Backbone X loaded: {len(x_df.columns)} variables.")
    except Exception as e:
        print(f"❌ FATAL: Failed to parse Backbone X: {e}"); sys.exit(1)

    # 4. Load Greenbook Targets Y
    try:
        y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
        if not y_files:
            print(f"❌ FATAL: No target files found in {processed_dir}")
            sys.exit(1)
            
        print(f"📦 Merging {len(y_files)} Greenbook target files...")
        y_df = pd.concat([
            pd.read_csv(os.path.join(processed_dir, f))
            .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
            .set_index('date') for f in y_files
        ], axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Failed to merge Target Y files: {e}"); sys.exit(1)

    # 5. In-Memory Merge & Solve
    from pyfrbus import frbus
    model_xml = os.path.join(working_dir, "models/model.xml")
    model = frbus.Frbus(model_xml)
    
    # Merge targets (Y) over backbone (X)
    combined_df = y_df.combine_first(x_df).sort_index()
    
    try:
        solve_start, solve_end = y_df.index.min(), y_df.index.max()
        print(f"📈 Solving for residuals 'e' from {solve_start} to {solve_end}...")
        
        # init_trac finds the e such that Y = model(Beta, X) + e
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # 6. Export Results
        res_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(res_path)
        print(f"✅ SUCCESS: Calibration complete. Residuals saved to {res_path}")
        
    except Exception as err:
        print(f"❌ Solver Error: {err}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()