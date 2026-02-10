import pandas as pd
import psutil
import sys
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data

def check_hardware_readiness():
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    print(f"🖥️  Hardware Check: {available_gb:.2f} GB RAM available.")
    if available_gb < 3.5:
        print("❌ ERROR: Insufficient RAM. FRB/US structural solving requires ~4GB.")
        sys.exit(1)

def run_pro_engine():
    check_hardware_readiness()

    start_date = "2015Q1"
    end_date = "2025Q3"
    
    print("🚀 Initializing FRB/US Structural Engine...")
    df = load_data("/home/spark/data/y_unemp.csv") 
    
    # Ensure XGAP exists
    if 'GAP' in df.columns: df['XGAP'] = df['GAP']

    # Use the absolute path we established in Jenkins
    model = Frbus("/home/spark/models/model.xml")

    # --- AUTO-FILL MISSING VARIABLES ---
    # Combine all variables the model expects (endogenous and exogenous)
    required_vars = set(model.endo_names) | set(model.exo_names)
    missing_vars = [v for v in required_vars if v not in df.columns]

    if missing_vars:
        print(f"⚠️  Filling {len(missing_vars)} missing variables with 0.0 (e.g., {missing_vars[:5]}...)")
        for var in missing_vars:
            df[var] = 0.0
    # -----------------------------------    

    print("⚖️  Solving for Tracking Residuals (e)...")
    
    # FIX: Clean positional arguments. 
    # Usually: init_trac(start, end, dataframe, mce)
    # We remove the "start=" and "end=" keywords to avoid syntax errors
    results = model.init_trac(start_date, end_date, df)

    print("🚀 Running Forecast Simulation...")
    # FIX: solve uses the exact same 3-argument structure
    output = model.solve(start_date, end_date, results)

    # --- JUDGMENT ALERT LOGIC ---
    threshold = 0.5
    # results is usually the dataframe returned by init_trac
    results['judgment_alert'] = results['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )

    # Identify the most recent alert
    alerts = results[results['judgment_alert'].str.contains('🚨')]
    if not alerts.empty:
        print(f"\n⚠️  ALERT: Detected {len(alerts)} quarters with high manual judgment.")
        print(alerts[['LUR_trac', 'judgment_alert']].tail(3))

    # Use absolute path for results too
    results.to_csv("/home/spark/results/final_judgment_report.csv")
    output.to_csv("/home/spark/results/final_simulation_forecast.csv")
    print("\n✅ Engine Run Complete. Report archived.")

if __name__ == "__main__":
    run_pro_engine()