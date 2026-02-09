import pandas as pd
import psutil
import sys
from pyfrbus.frbus import Frbus
from pyfrbus.frbus.load_data import load_data

def check_hardware_readiness():
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    print(f"🖥️  Hardware Check: {available_gb:.2f} GB RAM available.")
    if available_gb < 3.5:
        print("❌ ERROR: Insufficient RAM. FRB/US structural solving requires ~4GB.")
        sys.exit(1)

def run_pro_engine():
    check_hardware_readiness()
    
    print("🚀 Initializing FRB/US Structural Engine...")
    df = load_data("data/y_unemp.csv") 
    
    # Ensure XGAP exists (Common mapping fix)
    if 'GAP' in df.columns: df['XGAP'] = df['GAP']

    model = Frbus("models/model.xml")

    print("⚖️  Solving for Tracking Residuals (e)...")
    results = model.init_trac(data=df, start=2015.0, end=2025.75, mce=None)

    # --- JUDGMENT ALERT LOGIC ---
    # We look at LUR_trac (the add factor)
    threshold = 0.5
    results['judgment_alert'] = results['LUR_trac'].apply(
        lambda x: '🚨 HIGH JUDGMENT' if abs(x) > threshold else '✅ MODEL DRIVEN'
    )

    # Identify the most recent alert
    alerts = results[results['judgment_alert'].str.contains('🚨')]
    if not alerts.empty:
        print(f"\n⚠️  ALERT: Detected {len(alerts)} quarters with high manual judgment.")
        print(alerts[['LUR_trac', 'judgment_alert']].tail(3))

    results.to_csv("results/final_judgment_report.csv")
    print("\n✅ Build #53 Complete. Report archived.")

if __name__ == "__main__":
    run_pro_engine()