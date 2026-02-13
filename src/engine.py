import os
import sys
import pandas as pd
import traceback
from fetch_tealbook import fetch_and_verify_macro_data

def run_pipeline():
    print("\n" + "="*50)
    print("🚀 MACRO ENGINE: INTEGRATED PIPELINE")
    print("="*50)
    
    try:
        # STAGE 1: Data Fetching
        print("\n📡 STAGE 1: Processing Federal Reserve Data...")
        fetch_and_verify_macro_data()
        
        # Use absolute path to avoid working directory confusion
        processed_path = "/home/spark/data/tealbook_full_x.csv"
        
        if os.path.exists(processed_path):
            df = pd.read_csv(processed_path)
            print(f"✅ Success! Loaded data from {processed_path}")
            print(f"📊 Rows: {len(df)} | Columns: {list(df.columns)}")
            print("\n📥 DATA PREVIEW (Last 5 Quarters):")
            print(df.tail(5).to_string())
        else:
            print(f"❌ CRITICAL: {processed_path} missing.")
            sys.exit(1)

        # STAGE 2: Calibration
        print("\n🧪 STAGE 2: Running Calibration Engine...")
        # (Your math/solver logic goes here)
        print("✅ Stage 2 Complete.")

    except Exception as e:
        print(f"❌ PIPELINE CRASHED: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*50)
    print("🏁 SUCCESSful BUILD")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()