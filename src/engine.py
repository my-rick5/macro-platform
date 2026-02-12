import pandas as pd
import os
import sys

# Path Injection for Frbus
sys.path.insert(0, "/home/spark/pyfrbus")
try:
    from pyfrbus.frbus import Frbus
    print("✅ Frbus Module Loaded.")
except Exception as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def run_pro_engine():
    print("\n--- 🕵️ MULTI-VARIABLE HANDSHAKE (Build #816) ---")
    
    working_dir = "/home/spark"
    proc_dir = os.path.join(working_dir, "external_data")
    
    # 1. Load Backbone
    x_df = pd.read_csv(os.path.join(proc_dir, "longdata.csv"))
    x_df.columns = [c.lower().strip() for c in x_df.columns]
    x_df['date'] = pd.PeriodIndex(x_df['obs' if 'obs' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Variable Audit Loop
    core_vars = ['unemp', 'ffr', 'pce', 'gdp']
    combined_df = x_df.copy()
    
    for var in core_vars:
        file_path = os.path.join(proc_dir, f"{var}.csv")
        if not os.path.exists(file_path):
            print(f"⚠️ MISSING: {var}.csv")
            continue
            
        y_raw = pd.read_csv(file_path)
        y_raw.columns = [c.lower().strip() for c in y_raw.columns]
        
        # Prepare target DF
        y_df = y_raw[['date', var]].copy()
        y_df['date'] = pd.PeriodIndex(y_df['date'], freq='Q')
        y_df = y_df.set_index('date').sort_index()
        
        # Ensure column exists in backbone
        if var not in combined_df.columns:
            print(f"➕ Adding missing column '{var}' to backbone.")
            combined_df[var] = float('nan')

        # Overwrite Backbone with Preprocessed Data
        combined_df.update(y_df)
        
        # Sanity Check a recent date
        check_date = pd.Period('2019Q1', freq='Q')
        if check_date in combined_df.index:
            val = combined_df.loc[check_date, var]
            status = "✅" if not pd.isna(val) else "❌"
            print(f"   {status} {var.upper()} @ {check_date}: {val}")

    # 3. Solver Execution
    common = x_df.index.intersection(combined_df.index)
    start, end = common.min(), common.max()
    
    try:
        model = Frbus(os.path.join(working_dir, "models/model.xml"))
        print(f"\n📈 SOLVING: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        os.makedirs(os.path.dirname(res_path), exist_ok=True)
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"🏁 SUCCESS: Results saved to {res_path}")
        
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()