import pandas as pd
import os
import sys
import glob

def run_pro_engine():
    print("🚀 Heartbeat: Full Calibration Engine (Build #583)")
    
    # 1. Path Configuration
    working_dir = os.getcwd()
    data_dir = os.path.join(working_dir, "data")
    processed_dir = os.path.join(data_dir, "processed")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 2. Load X (Backbone: longdata.csv)
    # This provides the structural foundation and historical variables
    x_path = os.path.join(data_dir, "longdata.csv")
    if not os.path.exists(x_path):
        print(f"❌ FATAL: Backbone X not found at {x_path}")
        sys.exit(1)

    try:
        print(f"📦 Loading Backbone: {x_path}")
        x_df = pd.read_csv(x_path)
        # Convert OBS (1967Q1) or DATE (1967.1) to PeriodIndex
        if 'OBS' in x_df.columns:
            x_df['date'] = pd.PeriodIndex(x_df['OBS'], freq='Q')
        else:
            x_df['date'] = pd.PeriodIndex(x_df['date'], freq='Q')
            
        x_df = x_df.set_index('date').apply(pd.to_numeric, errors='coerce')
        x_df.columns = [c.lower() for c in x_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Error parsing Backbone X: {e}")
        sys.exit(1)

    # 3. Load Y (Targets: The 15 GBweb CSVs)
    # These are the projections we want to hit
    try:
        y_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv')]
        if not y_files:
            print(f"❌ FATAL: No target files found in {processed_dir}")
            sys.exit(1)
            
        print(f"📦 Loading {len(y_files)} Target variables from processed folder...")
        y_list = []
        for f in y_files:
            tmp = pd.read_csv(os.path.join(processed_dir, f))
            tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
            y_list.append(tmp.set_index('date'))
            
        y_df = pd.concat(y_list, axis=1).sort_index()
        y_df.columns = [c.lower() for c in y_df.columns]
    except Exception as e:
        print(f"❌ FATAL: Error parsing Target Y: {e}")
        sys.exit(1)

    # 4. In-Memory Merge (The X + e = Y Logic)
    # combined_df uses Backbone values as the base, overlaid by Target values
    print("🔄 Merging datasets in memory...")
    combined_df = y_df.combine_first(x_df).sort_index()

    # 5. Solve for e (Residuals)
    from pyfrbus import frbus
    model_path = os.path.join(working_dir, "models/model.xml")
    if not os.path.exists(model_path):
        print(f"❌ FATAL: Model XML not found at {model_path}")
        sys.exit(1)
        
    model = frbus.Frbus(model_path)
    
    # Define window based on your GB data range
    solve_start = y_df.index.min()
    solve_end = y_df.index.max()
    
    print(f"📈 Solving for residuals 'e' from {solve_start} to {solve_end}...")
    
    try:
        # init_trac finds the 'e' required to make the model align with your GB targets
        e_residuals = model.init_trac(solve_start, solve_end, combined_df)
        
        # Save the e values to the results folder
        output_path = os.path.join(results_dir, "calibration_residuals_e.csv")
        e_residuals.to_csv(output_path)
        
        print(f"✅ SUCCESS: Calibration complete.")
        print(f"📂 Residuals saved to: {output_path}")
        
    except Exception as err:
        print(f"❌ Solver Error: {err}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()