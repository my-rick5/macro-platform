import os
import sys
import pandas as pd

# 1. SETUP: Pathing logic to ensure imports work regardless of where Docker starts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

from fetch_tealbook import fetch_and_verify_macro_data

def run_pipeline():
    print("--- 🚀 Starting Macro Engine Pipeline ---")
    
    # Ensure standard directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    # --- STAGE 1: FETCH & DIAGNOSE ---
    try:
        print("📡 Stage 1: Fetching Tealbook Data...")
        
        # Execute the fetch script
        fetch_and_verify_macro_data()
        
        # Load for diagnostic check (assumes fetch_tealbook saves to this path)
        data_path = 'data/tealbook_raw.xlsx'
        if os.path.exists(data_path):
            df = pd.read_excel(data_path)
            print(f"📊 Data Received: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Fuzzy Logic for 'date' column
            # This looks for 'date', 'Date', 'DATE', or 'DATE '
            cols = {c.strip().lower(): c for c in df.columns}
            if 'date' in cols:
                actual_col_name = cols['date']
                print(f"✅ Found date column as: '{actual_col_name}'")
                df.sort_values(actual_col_name, inplace=True)
                # Standardize it to lowercase 'date' for the rest of the engine
                df.rename(columns={actual_col_name: 'date'}, inplace=True)
            else:
                print(f"⚠️ WARNING: No date column found! Available: {list(df.columns)}")
        else:
            print(f"❌ Error: {data_path} was not created by the fetch script.")
            sys.exit(1)

        print("✅ Data Fetch & Verification Complete.")
        
    except Exception as e:
        print(f"❌ Stage 1 Failed: {e}")
        # This prints the full error stack trace to Jenkins console
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # --- STAGE 2: CALIBRATION ENGINE ---
    try:
        print("🧪 Stage 2: Running Calibration Engine...")
        
        # TODO: Import and call your model/solver here
        # from model import run_solver
        # run_solver(df) 
        
        print("✅ Calibration Complete.")
    except Exception as e:
        print(f"❌ Stage 2 Failed: {e}")
        sys.exit(1)

    print("--- 🏁 All Systems Finished Successfully ---")

if __name__ == "__main__":
    run_pipeline()