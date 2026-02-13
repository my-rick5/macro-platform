import os
import sys
import pandas as pd
import traceback

# 1. SETUP: Ensure the project root is the context for all file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

from fetch_tealbook import fetch_and_verify_macro_data

def run_pipeline():
    print("\n" + "="*50)
    print("🚀 MACRO ENGINE PIPELINE STARTING")
    print("="*50)
    
    # Ensure directories exist (Fixes [Errno 2])
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    # --- STAGE 1: FETCH & DIAGNOSE ---
    try:
        print("\n📡 STAGE 1: Fetching Tealbook Data...")
        
        # This calls your script logic
        fetch_and_verify_macro_data()
        
        data_path = 'data/tealbook_raw.xlsx'
        if os.path.exists(data_path):
            df = pd.read_excel(data_path)
            
            # --- DEBUG SNAPSHOT ---
            print("\n--- 🔍 DATA DIAGNOSTIC SNAPSHOT ---")
            print(f"📍 Location: {data_path}")
            print(f"📏 Shape:    {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"📋 Columns:  {list(df.columns)}")
            print("\n📥 First 5 Rows of Data:")
            # to_string() ensures the full width prints in Jenkins logs
            print(df.head(5).to_string()) 
            print("-" * 35 + "\n")
            
            # Fuzzy Logic for 'date' column standardization
            # Looks for 'date', 'Date', 'DATE', etc.
            cols_map = {c.strip().lower(): c for c in df.columns}
            if 'date' in cols_map:
                actual_name = cols_map['date']
                print(f"✅ Found date column: '{actual_name}'. Standardizing...")
                df[actual_name] = pd.to_datetime(df[actual_name])
                df.sort_values(actual_name, inplace=True)
                df.rename(columns={actual_name: 'date'}, inplace=True)
            else:
                print(f"⚠️ WARNING: No 'date' column detected in {list(df.columns)}")
        else:
            print(f"❌ CRITICAL: {data_path} not found after fetch attempt.")
            sys.exit(1)

        print("✅ Stage 1 Complete: Data is ready.")
        
    except Exception as e:
        print(f"\n❌ STAGE 1 FAILED")
        print(f"Error Message: {str(e)}")
        print("\n--- 🛠️ TRACEBACK ---")
        traceback.print_exc()
        sys.exit(1)

    # --- STAGE 2: CALIBRATION ENGINE ---
    try:
        print("\n🧪 STAGE 2: Running Calibration Engine...")
        # Placeholder for your engine logic
        # from engine_logic import run_calibration
        # run_calibration(df)
        print("✅ Stage 2 Complete.")
    except Exception as e:
        print(f"❌ STAGE 2 FAILED: {e}")
        sys.exit(1)

    print("\n" + "="*50)
    print("🏁 PIPELINE FINISHED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()