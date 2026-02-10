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
    if available_gb < 3.0:
        print("❌ ERROR: Low Memory.")
        sys.exit(1)

def load_and_merge_data(processed_dir):
    all_files = glob.glob(os.path.join(processed_dir, "*.csv"))
    if not all_files:
        raise FileNotFoundError(f"🔍 No processed CSVs found in {processed_dir}")

    print(f"📂 Found {len(all_files)} variables. Merging into master matrix...")
    df_list = []
    for f in all_files:
        temp_df = pd.read_csv(f, index_col=0)
        temp_df.index = pd.PeriodIndex(temp_df.index, freq='Q')
        df_list.append(temp_df)
    
    return pd.concat(df_list, axis=1)

def run_pro_engine():
    check_hardware()
    
    # 1. Load merged data
    processed_path = "/home/spark/data/processed"
    df = load_and_merge_data(processed_path)
    
    start_date = df.index[0]
    end_date = df.index[-1]
    print(f"📅 Simulation Window: {start_date} to {end_date}")

    # 2. Initialize Model
    model = Frbus("/home/spark/models/model.xml")

    # 3. Auto-Fill missing variables to prevent Whac-A-Mole
    required_vars = set(model.endo_names) | set(model.exo_names)
    missing_vars = [v for v in required_vars if v not in df.columns]
    
    if missing_vars:
        print(f"⚠️  Filling {len(missing_vars)} missing variables with 0.0...")
        zero_df = pd.DataFrame(0.0, index=df.index, columns=missing_vars)
        df = pd.concat([df, zero_df], axis=1)

    # 4. Solve for Judgment (Residuals)
    print("⚖️  Solving for Tracking Residuals (Judgment)...")
    results = model.init_trac(start_date, end_date, df)

    # 5. Run Final Forecast
    print("🚀 Running Forecast Simulation...")
    output = model.solve(start_date, end_date, results)

    # 6. Judgment Alert Logic
    threshold = 0.5
    if 'LUR_trac' in results.columns:
        results['judgment_alert'] = results['LUR_trac'].apply(
            lambda x: '🚨 HIGH' if abs(x) > threshold else '✅ OK'
        )
    
    # 7. Save Reports
    results.to_csv("/home/spark/results/final_judgment_report.csv")
    output.to_csv("/home/spark/results/final_simulation_forecast.csv")
    print("\n✅ Engine Run Complete. Reports archived.")

if __name__ == "__main__":
    run_pro_engine()