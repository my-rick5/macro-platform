import pandas as pd
import os
import sys
import glob

# --- PATH INJECTION ---
sys.path.insert(0, "/home/spark/pyfrbus")
try:
    from pyfrbus.frbus import Frbus
    print("✅ Frbus Loaded.")
except Exception as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def run_pro_engine():
    print("\n--- 🕵️ DATA FORENSICS START (Build #814) ---")
    
    working_dir = "/home/spark"
    proc_dir = os.path.join(working_dir, "external_data")
    
    # 1. Inspect Backbone (longdata)
    longdata_path = os.path.join(proc_dir, "longdata.csv")
    x_df = pd.read_csv(longdata_path)
    x_df.columns = [c.lower() for c in x_df.columns]
    x_df['date'] = pd.PeriodIndex(x_df['obs' if 'obs' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index().copy()
    print(f"📋 Backbone (x_df) Shape: {x_df.shape} | Range: {x_df.index.min()} to {x_df.index.max()}")

    # 2. Inspect Target CSVs (unemp.csv, etc.)
    target_files = [f for f in glob.glob(os.path.join(proc_dir, "*.csv")) if "longdata.csv" not in os.path.basename(f)]
    
    y_dfs = []
    for f in target_files:
        temp = pd.read_csv(f)
        fname = os.path.basename(f)
        
        # DEBUG: Check for the "Date Stamp" bug inside the engine
        max_val = temp.iloc[:, 1].max()
        print(f"🔍 Checking {fname}: Max Value = {max_val}")
        if max_val > 1000:
            print(f"   🚨 ALERT: {fname} STILL CONTAINS DATE STAMPS (>1000)!")

        temp['date'] = pd.PeriodIndex(temp['date'], freq='Q')
        temp = temp.set_index('date')
        y_dfs.append(temp)
    
    # 3. The Merge - Diagnostic Check
    y_df = pd.concat(y_dfs, axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]
    print(f"📋 Combined Targets (y_df) Shape: {y_df.shape}")

    # 4. The Priority Handshake
    # We test if unemp is present in BOTH and which one survives
    combined_df = y_df.combine_first(x_df).sort_index()
    
    if 'unemp' in combined_df.columns:
        u_val = combined_df['unemp'].iloc[0]
        print(f"🧪 Handshake Audit: 'unemp' first value in combined_df is {u_val}")
        if u_val > 1000:
            print("   🚨 FAIL: 'unemp' in combined_df is a date stamp. x_df likely overwrote y_df or y_df was empty.")

    # 5. Solver Execution
    common = x_df.index.intersection(y_df.index)
    start, end = common.min(), common.max()
    print(f"📈 Solving Window: {start} to {end}")

    model = Frbus(os.path.join(working_dir, "models/model.xml"))
    
    try:
        e_residuals = model.init_trac(start, end, combined_df)
        
        # FINAL DIAGNOSTIC: Check the output before saving
        res_col = 'unemp' # Or whatever the solver names the residual column
        if res_col in e_residuals.columns:
            final_check = e_residuals.loc[start, res_col]
            print(f"🏁 FINAL CHECK: First solved residual for {res_col} is {final_check}")
            
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"💾 Saved to {res_path}")
        
    except Exception as e:
        print(f"❌ Solver Failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()