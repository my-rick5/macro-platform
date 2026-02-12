import pandas as pd
import os
import sys
import glob

# --- THE PATH INJECTION FIX ---
# Force the container to find the hidden 'frbus' module.
sys.path.insert(0, "/home/spark/pyfrbus")

try:
    from pyfrbus import frbus
    from pyfrbus.frbus import Frbus
    print("✅ Successfully imported Frbus via absolute path injection.")
except ImportError as e:
    print(f"❌ Initial import failing: {e}")
    try:
        sys.path.append("/home/spark/pyfrbus/pyfrbus")
        import frbus
        from frbus import Frbus
        print("✅ Successfully imported Frbus via inner-path override.")
    except Exception as e2:
        print(f"❌ FATAL: {e2}")
        sys.exit(1)

def audit_data_sources(proc_dir):
    """Prints timestamps and metadata of CSVs found in the target directory."""
    print("\n🔍 --- ENGINE DATA AUDIT (Build #813) ---")
    y_files = glob.glob(os.path.join(proc_dir, "*.csv"))
    
    if not y_files:
        print(f"⚠️ WARNING: No CSV files found in {proc_dir}")
        return

    for path in y_files:
        if "longdata.csv" in path: continue
        try:
            df_check = pd.read_csv(path)
            ts = df_check['processed_at'].iloc[0] if 'processed_at' in df_check.columns else "❌ NO TIMESTAMP"
            # Get first non-NaN value to verify if it's a date or a residual
            sample_val = df_check.iloc[0, 1] 
            print(f"✅ LOADING: {os.path.basename(path)}")
            print(f"   🕒 Processed At: {ts}")
            print(f"   📊 Sample Value: {sample_val}")
        except Exception as e:
            print(f"   ⚠️ Could not audit {path}: {e}")
    print("------------------------------------------\n")

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #813 Solver-Ready)")
    
    working_dir = "/home/spark"
    proc_dir = os.path.join(working_dir, "external_data")
    
    # 1. Audit Data Before Processing
    # This will prove if unemp.csv has the dates or the correct residuals
    audit_data_sources(proc_dir)
    
    # 2. Load & De-fragment Backbone (Longdata)
    longdata_path = os.path.join(proc_dir, "longdata.csv")
    if not os.path.exists(longdata_path):
        print(f"❌ FATAL: Missing backbone file at {longdata_path}")
        sys.exit(1)
        
    x_df = pd.read_csv(longdata_path)
    x_df.columns = [c.lower() for c in x_df.columns]
    
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    x_df = x_df.set_index('date').sort_index().copy()

    # 3. Load Processed Targets
    target_files = [f for f in glob.glob(os.path.join(proc_dir, "*.csv")) if "longdata.csv" not in os.path.basename(f)]
    
    print(f"📊 Concatenating target files: {[os.path.basename(f) for f in target_files]}")
    
    # We use sort_index() and lower() to ensure the merge is clean
    y_list = []
    for f in target_files:
        temp = pd.read_csv(f)
        temp['date'] = pd.PeriodIndex(temp['date'], freq='Q')
        temp = temp.set_index('date')
        y_list.append(temp)
    
    y_df = pd.concat(y_list, axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 4. Solve Initialization (The Handshake)
    # y_df (your new residuals) takes priority over x_df (historical backbone)
    combined_df = y_df.combine_first(x_df).sort_index()
    
    common = x_df.index.intersection(y_df.index)
    if common.empty:
        print("❌ ERROR: No overlapping dates between longdata and processed targets.")
        sys.exit(1)
        
    start, end = common.min(), common.max()
    model_path = os.path.join(working_dir, "models/model.xml")
    
    # Initialize the Solver
    model = Frbus(model_path)
    
    try:
        print(f"📈 Solving init_trac: {start} to {end}")
        # The solver creates its own residuals based on the combined_df
        e_residuals = model.init_trac(start, end, combined_df)
        
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        os.makedirs(os.path.dirname(res_path), exist_ok=True)
        
        # Export only the solved window
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported residuals to {res_path}")
        
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}")
        # Print a snippet of the data that caused the crash for debugging
        print("DEBUG: combined_df snippet:")
        print(combined_df.head(5))
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()