import pandas as pd
import os
import sys

def run_pro_engine():
    print("\n--- 🕵️ CORE VARIABLE AUDIT (Build #815) ---")
    
    working_dir = "/home/spark"
    proc_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone
    x_df = pd.read_csv(os.path.join(proc_dir, "longdata.csv"))
    x_df.columns = [c.lower() for c in x_df.columns]
    x_df['date'] = pd.PeriodIndex(x_df['obs' if 'obs' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Load and CLEAN Target (unemp.csv)
    unemp_path = os.path.join(proc_dir, "unemp.csv")
    raw_y = pd.read_csv(unemp_path)
    
    print(f"📥 RAW INPUT (unemp.csv):\n{raw_y.head(3).to_string(index=False)}")
    
    # FIX: Drop metadata columns like 'processed_at' so they don't bloat the DF
    # This explains why you saw "2" y-values earlier.
    cols_to_keep = [c for c in raw_y.columns if c.lower() in ['date', 'unemp']]
    y_df = raw_y[cols_to_keep].copy()
    y_df['date'] = pd.PeriodIndex(y_df['date'], freq='Q')
    y_df = y_df.set_index('date').sort_index()

    print(f"\n🧪 CLEAN TARGET (y_df):\n{y_df.head(3)}")

    # 3. The Handshake (Merging Backbone + Targets)
    # Using 'update' to force our new values into the backbone
    combined_df = x_df.copy()
    combined_df.update(y_df) 
    
    print(f"\n🤝 AFTER MERGE (combined_df - unemp column):")
    print(combined_df['unemp'].dropna().head(5))

    # 4. Run Solver
    common = x_df.index.intersection(y_df.index)
    start, end = common.min(), common.max()
    
    from pyfrbus.frbus import Frbus
    model = Frbus(os.path.join(working_dir, "models/model.xml"))
    
    try:
        print(f"\n📈 SOLVING: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        
        # Check if the solver output actually matches our input
        if 'unemp' in e_residuals.columns:
            print(f"🏁 SOLVER OUTPUT (unemp residuals):\n{e_residuals['unemp'].loc[start:start+2]}")
            
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ Saved results to {res_path}")
        
    except Exception as e:
        print(f"❌ Solver Error: {e}")

if __name__ == "__main__":
    run_pro_engine()