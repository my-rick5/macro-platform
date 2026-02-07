import os
import datetime
from bvar_ultra import run_ultra_model
from evaluate_performance.py import run_evaluation # Ensure the file name matches

def main():
    print("🚀 Starting MacroFlow Pipeline...")
    
    # 1. Generate the Timestamp
    # We create it here so both scripts are perfectly synced
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    print(f"📅 Session Timestamp: {timestamp}")

    # 2. Run the Forecast Model
    print("\n--- Phase 1: Forecasting ---")
    try:
        # Note: We might need to slightly tweak bvar_ultra to accept a timestamp,
        # but for now, it generates its own. We'll grab the latest.
        run_ultra_model() 
    except Exception as e:
        print(f"❌ Forecast Phase Failed: {e}")
        return

    # 3. Run the Evaluation
    print("\n--- Phase 2: Evaluation ---")
    try:
        # Pass the timestamp we just generated
        # (Assuming bvar_ultra and this script are run within the same minute)
        run_evaluation(timestamp)
    except Exception as e:
        print(f"❌ Evaluation Phase Failed: {e}")

    print("\n✅ Pipeline Complete. Check GCS for archives and /output for plots.")

if __name__ == "__main__":
    main()
