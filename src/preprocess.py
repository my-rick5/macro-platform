import pandas as pd
import psutil
import glob
import os
import sys
from pyfrbus.frbus import Frbus

def check_hardware():
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    print(f"🖥️  Hardware Check: {available_gb:.2f} GB RAM available.")
    if available_gb < 2.0:
        print("❌ ERROR: Insufficient Memory for FRB/US solve.")
        sys.exit(1)

def load_and_merge_data(processed_dir):
    """
    Collects all individual variable CSVs from the preprocessor 
    and merges them into a single Master Matrix.
    """
    all_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    if not all_files:
        raise FileNotFoundError(f"🔍 No processed CSVs found in {processed_dir}. Ensure preprocess.py ran successfully.")

    print(f"📂 Found {len(all_files)} variable files. Merging...")
    df_list = []
    
    for f in all_files:
        var_name = os.path.basename(f).replace('.csv', '').upper()
        temp_df = pd.read_csv(f, index_col=0)
        temp_df.index = pd.PeriodIndex(temp_df.index, freq='Q')
        df_list.append(temp_df)
    
    master_df = pd.concat(df_list, axis=1)

    # --- VERIFICATION PRINT STEP ---
    print("\n📊 --- MASTER DATA MATRIX VERIFICATION ---")
    print(f"Total Dimensions: {master_df.shape[0]} Quarters x {master_df.shape[1]} Variables")
    print(f"Variables Found: {', '.join(list(master_df.columns))}")
    print(f"Date Range: {master_df.index[0]} to {master_df.index[-1]}")
    print("\nFirst 3 rows of data:")
    print(master_df.head(3))
    print("-------------------------------------------\n")
    
    return master_df

def run_pro_engine():
    check_hardware()
    
    # 1. Load and verify the merged data
    processed_path = "/home/spark/data/processed"
    try:
        df = load_and_merge_data(processed_path)
    except Exception as e:
        print(f"❌ Data Load Error: {e}")
        sys.exit(1)
    
    start_date = df.index[0]
    end_date = df.index[-1]

    # 2. Model Setup
    print(f"🏗️  Loading FRB/US Model XML...")
    model = Frbus("/home/spark/models/model.xml")

    # 3. Auto-Fill for Stability (The 'Whac-A-Mole' fix)
    required_vars = set(model.endo_names) | set(model.exo_names)
    missing_vars = [v for v in required_vars if v not in df.columns]
    
    if missing_vars:
        print(f"⚠️  {len(missing_vars)} variables missing from Fed data. Filling with 0.0 for stability.")
        zero_df = pd.DataFrame(0.0, index=df.index, columns=missing_vars)
        df = pd.concat([df, zero_df], axis=1)

    # 4. Solve for Judgment (init_trac)
    print(f"⚖️  Solving for Tracking Residuals ({start_date} to {end_date})...")
    try:
        results = model.init_trac(start_date, end_date, df)
        
        # 5. Run Final Simulation
        print("🚀 Running Forecast Simulation...")
        output = model.solve(start_date, end_date, results)
        
        # 6. Export Results
        os.makedirs("/home/spark/results", exist_ok=True)
        results.to_csv("/home/spark/results/final_judgment_report.csv")
        output.to_csv("/home/spark/results/final_simulation_forecast.csv")
        
        print("\n✅ Build Successful.")
        print(f"📝 Reports generated: judgment_report.csv, simulation_forecast.csv")
        
    except Exception as e:
        print(f"❌ Engine Solve Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()