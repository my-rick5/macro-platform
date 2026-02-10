import pandas as pd
import os
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    print(f"🔍 Searching for data in: {data_path}")
    
    # Load and merge all CSVs
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    data_frames = []
    
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))

    # THE FIX: Merge and explicitly sort the index
    df = pd.concat(data_frames, axis=1).sort_index()

    # Calculate overlapping window
    df_overlap = df.dropna()
    if df_overlap.empty:
        # Fallback: if no perfect overlap, use the widest possible range 
        # with model-stability padding (filling NaNs with 0)
        start_date = df.index.min()
        end_date = df.index.max()
        df = df.fillna(0.0) 
    else:
        start_date = df_overlap.index.min()
        end_date = df_overlap.index.max()

    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}")
    print(f"Timeline: {start_date} to {end_date}")
    
    # Initialize Engine
    model = frbus.Frbus(model_path="/home/spark/models/model.xml")
    
    try:
        # Pass the validated, sorted dates to the solver
        results = model.init_trac(start_date, end_date, df)
        print("✅ Engine Solve Successful.")
        results.to_csv("/home/spark/results/residuals.csv")
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()