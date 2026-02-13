import os
import sys
import pandas as pd
import traceback

# 1. SETUP: Absolute pathing to ensure directories are created in /home/spark
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

from fetch_tealbook import fetch_and_verify_macro_data

def run_pipeline():
    print("\n" + "="*50)
    print("🚀 MACRO ENGINE PIPELINE STARTING")
    print("="*50)
    
    # FIX: Explicitly create the missing 'data' directory before fetching
    # This prevents the [Errno 2] error seen in the console logs
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    # --- STAGE 1: FETCH & DIAGNOSE ---
    try:
        print("\n📡 STAGE 1: Fetching Tealbook Data...")
        fetch_and_verify_macro_data()
        
        processed_path = "data/tealbook_full_x.csv"
        if os.path.exists(processed_path):
            df = pd.read_excel(processed_path)
            
            # --- DEBUG SNAPSHOT ---
            print("\n--- 🔍 DATA DIAGNOSTIC SNAPSHOT ---")
            print(f"📍 File Found: {processed_path}")
            print(f"📏 Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"📋 Columns:    {list(df.columns)}")
            print("\n📥 Data Preview (Top 5):")
            print(df.head(5).to_string()) 
            print("-" * 35 + "\n")
            
            # Fuzzy Logic for 'date' column standardization
            cols_map = {c.strip().lower(): c for c in df.columns}
            if 'date' in cols_map:
                actual_name = cols_map['date']
                print(f"✅ Normalizing date column: '{actual_name}'")
                df[actual_name] = pd.to_datetime(df[actual_name])
                df.sort_values(actual_name, inplace=True)
                df.rename(columns={actual_name: 'date'}, inplace=True)
            else:
                print(f"⚠️ WARNING: 'date' not found in: {list(df.columns)}")
        else:
            print(f"❌ CRITICAL: {processed_path} was not created. Check network/URL.")
            sys.exit(1)

        print("✅ Stage 1 Complete: Data loaded successfully.")
        
    except Exception as e:
        print(f"\n❌ STAGE 1 FAILED")
        print(f"Error Message: {str(e)}")
        print("\n--- 🛠️ TRACEBACK ---")
        traceback.print_exc()
        sys.exit(1)

    # --- STAGE 2: ENGINE LOGIC ---
    try:
        print("\n🧪 STAGE 2: Running Calibration...")
        # Your engine logic here
        print("✅ Stage 2 Complete.")
    except Exception as e:
        print(f"❌ STAGE 2 FAILED: {e}")
        sys.exit(1)

    print("\n" + "="*50)
    print("🏁 PIPELINE FINISHED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()