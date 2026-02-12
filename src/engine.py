import pandas as pd
import os
import sys
import glob

# --- THE PATH INJECTION FIX ---
# We force the container to look into the sub-folders to find the hidden 'frbus' module.

sys.path.append("/home/spark/pyfrbus")

try:
    # This reaches through the outer folder into the inner 'pyfrbus' package
    from pyfrbus import frbus
    from pyfrbus.frbus import Frbus
    print("✅ Successfully imported Frbus via absolute path injection.")
except ImportError as e:
    print(f"❌ Still failing. Detailed Error: {e}")
    # Fallback to the most direct possible import
    try:
        sys.path.append("/home/spark/pyfrbus/pyfrbus")
        import frbus
        from frbus import Frbus
        print("✅ Successfully imported Frbus via inner-path override.")
    except Exception as e2:
        print(f"❌ FATAL: {e2}")
        sys.exit(1)

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #763 Solver-Ready)")
    
    working_dir = "/home/spark"
    proc_dir = "external_data" 
    ext_dir = "external_data"
    
    # 1. Load & De-fragment Backbone
    longdata_path = os.path.join(working_dir, ext_dir, "longdata.csv")
    x_df = pd.read_csv(longdata_path)
    x_df.columns = [c.lower() for c in x_df.columns]
    
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    
    # .copy() fixes the PerformanceWarning seen in Build #762
    x_df = x_df.set_index('date').sort_index().copy()

    # 2. Load Processed Targets
    y_files = glob.glob(os.path.join(working_dir, proc_dir, "*.csv"))
    target_files = [f for f in y_files if "longdata.csv" not in os.path.basename(f)]
    
    print(f"📊 Loading target files: {[os.path.basename(f) for f in target_files]}")
    
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in target_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. Solve Initialization
    combined_df = y_df.combine_first(x_df).sort_index()
    common = x_df.index.intersection(y_df.index)
    start, end = common.min(), common.max()
    
    model_path = os.path.join(working_dir, "models/model.xml")
    
    # Initialize the class using the robust import from the top
    model = Frbus(model_path)
    
    try:
        print(f"📈 Solving init_trac: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported residuals to {res_path}")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()