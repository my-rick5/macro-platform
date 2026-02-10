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

    # 3. THE FIX: Inject missing model-required variables
    # 'dmptmax' is a standard policy variable; we'll default it to 2.0 (2% target)
    if 'dmptmax' not in df.columns:
        print("⚠️  Injecting missing model variable: dmptmax (defaulting to 2.0)")
        df['dmptmax'] = 2.0

    # Ensure no NaN gaps exist in the matrix
    df = df.ffill().bfill().fillna(0.0)

    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}")
    print(f"Timeline: {start_date} to {end_date}")
    
    # 4. Initialize and Solve
    try:
        model = frbus.Frbus("/home/spark/models/model.xml")
        print("🏗️  Model XML Loaded Successfully.")
        
        results = model.init_trac(start_date, end_date, df)
        print("✅ Engine Solve Successful.")
        
        os.makedirs("/home/spark/results", exist_ok=True)
        results.to_csv("/home/spark/results/residuals.csv")
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()