import pandas as pd
import os
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    print(f"🔍 Searching for data in: {data_path}")
    
    # 1. Load and merge all CSVs
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))

    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. Identify the solver window
    df_overlap = df.dropna()
    start_date = df_overlap.index.min() if not df_overlap.empty else df.index.min()
    end_date = df_overlap.index.max() if not df_overlap.empty else df.index.max()

    # 3. Initialize Model and Safely Inspect Variables
    try:
        model = frbus.Frbus("/home/spark/models/model.xml")
        print("🏗️  Model XML Loaded Successfully.")
        
        # Correct way to get variable names in pyfrbus
        expected_vars = list(model.lookup.keys()) 
        missing_vars = [v for v in expected_vars if v not in df.columns]
        
        if missing_vars:
            print(f"⚠️  Injecting {len(missing_vars)} missing variables...")
            for var in missing_vars:
                # Targeted defaults for policy variables
                if 'dmpt' in var:
                    df[var] = 2.0  # Inflation/Unemp targets
                elif 'delrff' in var:
                    df[var] = 3.0  # Fed Funds Rate
                else:
                    df[var] = 0.0  # Zero out residuals/others
        
        # 4. Final Data Clean-up
        df = df.ffill().bfill().fillna(0.0)

        print(f"\n📊 --- MASTER DATA MATRIX ---")
        print(f"Total Shape: {df.shape}")
        print(f"Timeline: {start_date} to {end_date}")
        
        # 5. Solve for Residuals
        results = model.init_trac(start_date, end_date, df)
        print("✅ Engine Solve Successful.")
        
        os.makedirs("/home/spark/results", exist_ok=True)
        results.to_csv("/home/spark/results/residuals.csv")
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()