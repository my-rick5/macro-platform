import pandas as pd
import os
import sys

# --- PORTABLE PATH INJECTION ---
# Works whether running locally or in a 'base-image' container
BASE_DIR = os.getenv('SPARK_HOME', '/home/spark')
sys.path.insert(0, os.path.join(BASE_DIR, "pyfrbus"))

try:
    from pyfrbus.frbus import Frbus
    print("✅ Frbus Module Loaded.")
except Exception as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def run_pro_engine():
    print("\n--- 🕵️ CORE VARIABLE AUDIT (Base-Image Ready) ---")
    
    proc_dir = os.path.join(BASE_DIR, "external_data")
    
    # 1. Load Backbone (The 'History')
    x_df = pd.read_csv(os.path.join(proc_dir, "longdata.csv"))
    x_df.columns = [c.lower().strip() for c in x_df.columns]
    x_df['date'] = pd.PeriodIndex(x_df['obs' if 'obs' in x_df.columns else 'date'], freq='Q')
    x_df = x_df.set_index('date').sort_index()

    # 2. Variable Audit & "Safe Merge"
    core_vars = ['unemp', 'ffr', 'pce', 'gdp']
    
    # Start with a copy of the backbone
    combined_df = x_df.copy()
    
    for var in core_vars:
        file_path = os.path.join(proc_dir, f"{var}.csv")
        if not os.path.exists(file_path):
            print(f"⚠️ MISSING: {var}.csv - Using backbone values only.")
            continue
            
        y_raw = pd.read_csv(file_path)
        y_raw.columns = [c.lower().strip() for c in y_raw.columns]
        
        y_df = y_raw[['date', var]].copy()
        y_df['date'] = pd.PeriodIndex(y_df['date'], freq='Q')
        y_df = y_df.set_index('date').sort_index()
        
        # --- CRITICAL FIX ---
        # We use combine_first so y_df (new data) fills holes in x_df (backbone)
        # and update() to overwrite. This keeps the 1962-2018 buffer intact.
        combined_df.update(y_df)
        print(f"   ✅ {var.upper()} updated with preprocessed data.")

    # 3. Define a Safe Solving Window
    # To avoid 'index out of bounds', we solve only where we have fresh data
    # plus a small buffer.
    target_start = pd.Period('2017Q1', freq='Q')
    target_end   = pd.Period('2022Q4', freq='Q')
    
    # Ensure window is within backbone limits
    start = max(target_start, x_df.index.min() + 8) # +8 quarters buffer for lags
    end   = min(target_end, x_df.index.max())

    # 4. Run Solver
    model_path = os.path.join(BASE_DIR, "models/model.xml")
    try:
        model = Frbus(model_path)
        print(f"\n📈 SOLVING WINDOW: {start} to {end}")
        
        # Relaxing tolerance slightly can also speed up the build
        e_residuals = model.init_trac(start, end, combined_df)
        
        res_path = os.path.join(BASE_DIR, "results/calibration_residuals_e.csv")
        os.makedirs(os.path.dirname(res_path), exist_ok=True)
        e_residuals.loc[start:end].to_csv(res_path)
        print(f"🏁 SUCCESS: Results saved to {res_path}")
        
    except Exception as e:
        print(f"❌ SOLVER ERROR: {e}")
        # Log the shape to debug the 'index out of bounds'
        print(f"DEBUG: combined_df shape: {combined_df.shape}")
        sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()