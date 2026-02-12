import pandas as pd
import os
import sys
import glob

sys.path.append(os.path.join(os.getcwd(), "pyfrbus"))

try:
    # Attempt to reach the class inside the nested folder
    from pyfrbus import frbus
    print("✅ Successfully imported Frbus from nested pyfrbus.pyfrbus")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Trying fallback import...")
    try:
        from pyfrbus.frbus import Frbus
        print("✅ Successfully imported Frbus from pyfrbus.frbus")
    except ImportError as e2:
        print(f"❌ FATAL: Could not find Frbus class. {e2}")
        sys.exit(1)

def run_pro_engine():
    print("🚀 Heartbeat: Calibration Engine (Build #758)")
    
    working_dir = "/home/spark"
    proc_dir = "external_data" 
    ext_dir = "external_data"
    
    # 1. Load Backbone
    longdata_path = os.path.join(working_dir, ext_dir, "longdata.csv")
    x_df = pd.read_csv(longdata_path)
    x_df.columns = [c.lower() for c in x_df.columns]
    date_col = 'obs' if 'obs' in x_df.columns else 'date'
    x_df['date'] = pd.PeriodIndex(x_df[date_col], freq='Q')
    x_df = x_df.set_index('date').sort_index().copy()

    # 2. Load Targets
    search_path = os.path.join(working_dir, proc_dir, "*.csv")
    y_files = glob.glob(search_path)
    target_files = [f for f in y_files if "longdata.csv" not in os.path.basename(f)]
    
    print(f"📊 Targets found: {[os.path.basename(f) for f in target_files]}")
    
    y_df = pd.concat([
        pd.read_csv(f).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') 
        for f in target_files
    ], axis=1).sort_index()
    y_df.columns = [c.lower() for c in y_df.columns]

    # 3. Solver Logic
    combined_df = y_df.combine_first(x_df).sort_index()
    common = x_df.index.intersection(y_df.index)
    start, end = common.min(), common.max()
    
    model_path = os.path.join(working_dir, "models/model.xml")
    # Initialize the class we imported at the top
    model = Frbus(model_path)
    
    try:
        print(f"📈 Solving: {start} to {end}")
        e_residuals = model.init_trac(start, end, combined_df)
        res_path = os.path.join(working_dir, "results/calibration_residuals_e.csv")
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"✅ SUCCESS: Exported results.")
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()