import os
import sys
import pandas as pd
import traceback

# 1. SETUP: Standardize paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

from fetch_tealbook import fetch_and_verify_macro_data

def run_pipeline():
    print("\n" + "="*50)
    print("🚀 MACRO ENGINE: INTEGRATED PIPELINE")
    print("="*50)
    
    # --- STAGE 1: DATA PREPARATION ---
    try:
        print("\n📡 STAGE 1: Processing Federal Reserve Data...")
        fetch_and_verify_macro_data()
        
        # ✅ FIX: Read the CSV produced by the fetcher (not an Excel file)
        processed_path = "data/tealbook_full_x.csv"
        
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            print(f"✅ Success! Loaded processed data from {processed_path}")
            
            # Diagnostic Snapshot
            print(f"📊 Rows: {len(df)} | Columns: {list(df.columns)}")
            print("\n📥 DATA PREVIEW (Last 5 Quarters):")
            print(df.tail(5).to_string())
            print("-" * 30)
        else:
            print(f"❌ CRITICAL: {processed_path} missing. Stage 1 failed.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ STAGE 1 CRASHED: {e}")
        traceback.print_exc()
        sys.exit(1)

    # --- STAGE 2: CALIBRATION ---
    try:
        print("\n🧪 STAGE 2: Running Calibration Engine...")
        if df.empty:
            raise ValueError("DataFrame is empty. Cannot run calibration.")
            
        # Your engine logic here
        print("✅ Stage 2 Complete.")
    except Exception as e:
        print(f"❌ STAGE 2 CRASHED: {e}")
        sys.exit(1)

    print("\n" + "="*50)
    print("🏁 PIPELINE SUCCESS")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()