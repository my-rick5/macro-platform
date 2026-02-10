import pandas as pd
import psutil
import glob
import os
import sys
from pyfrbus.frbus import Frbus

def check_hardware():
    """Ensures the container has enough overhead for the FRB/US solver."""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    print(f"🖥️  Hardware Check: {available_gb:.2f} GB RAM available.")
    if available_gb < 2.0:
        print("❌ ERROR: Insufficient Memory (under 2GB). Solver may crash.")
        sys.exit(1)

def load_and_merge_data(processed_dir):
    """
    Scans for processed CSVs, merges them into a single matrix, 
    and prints a verification report to the console.
    """
    print(f"🔍 Searching for data in: {processed_dir}")
    all_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    
    if not all_files:
        # Fallback check for current directory if the mount path is weird
        print("⚠️  Target directory empty. Checking local data folder...")
        all_files = glob.glob("data/processed/*.csv")

    if not all_files:
        raise FileNotFoundError(f"🔍 No processed CSVs found. Preprocessing may have failed.")

    print(f"📂 Found {len(all_files)} variables. Merging into master matrix...")
    df_list = []
    for f in all_files:
        # Force variable name from filename (e.g., lur.csv -> LUR)
        var_name = os.path.basename(f).replace('.csv', '').upper()
        temp_df = pd.read_csv(f, index_col=0)
        temp_df.index = pd.PeriodIndex(temp_df.index, freq='Q')
        temp_df.columns = [var_name] # Ensure column name matches filename
        df_list.append(temp_df)
    
    master_df = pd.concat(df_list, axis=1)

    # --- VERIFICATION PRINT ---
    print("\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {master_df.shape} (Rows x Columns)")
    print(f"Variables Found: {list(master_df.columns)}")
    print(f"Timeline: {master_df.index[0]} to {master_df.index[-1]}")
    print("\nSample Data (First 3 rows):")
    print(master_df.head(3))
    print("---------------------------\n")
    
    return master_df

def run_pro_engine():
    check_hardware()
    
    # 1. Load merged data
    processed_path = "/home/spark/data/processed"
    try:
        df = load_and_merge_data(processed_path)
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        sys.exit(1)
    
    start_date = df.index[0]
    end_date = df.index[-1]

    # 2. Initialize Model
    print(f"🏗️  Loading Model XML...")
    model = Frbus("/home/spark/models/model.xml")

    # 3. Auto-Fill missing variables to prevent 'Whac-A-Mole' errors
    required_vars = set(model.endo_names) | set(model.exo_names)
    missing_vars = [v for v in required_vars if v not in df.columns]
    
    if missing_vars:
        print(f"⚠️  Filling {len(missing_vars)} missing variables with 0.0 for model stability...")
        zero_df = pd.DataFrame(0.0, index=df.index, columns=missing_vars)
        df = pd.concat([df, zero_df], axis=1)

    # 4. Solve for Judgment (Tracking Residuals)
    print(f"⚖️  Solving for Tracking Residuals (Judgment) from {start_date} to {end_date}...")
    results = model.init_trac(start_date, end_date, df)

    # 5. Run Final Forecast
    print("🚀 Running Forecast Simulation...")
    output = model.solve(start_date, end_date, results)

    # 6. Judgment Alert Logic (LUR focus)
    threshold = 0.5
    if 'LUR_trac' in results.columns:
        results['judgment_alert'] = results['LUR_trac'].apply(
            lambda x: '🚨 HIGH' if abs(x) > threshold else '✅ OK'
        )
    
    # 7. Save Reports
    os.makedirs("/home/spark/results", exist_ok=True)
    results.to_csv("/home/spark/results/final_judgment_report.csv")
    output.to_csv("/home/spark/results/final_simulation_forecast.csv")
    
    print("\n✅ Engine Run Complete. Reports saved to /home/spark/results/")

if __name__ == "__main__":
    run_pro_engine()