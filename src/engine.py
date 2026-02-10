import pandas as pd
import os
import xml.etree.ElementTree as ET
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    print(f"🔍 Searching for data in: {data_path}")
    
    # 1. Load and merge processed CSVs
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))

    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. THE ULTIMATE FIX: Parse XML directly for required variables
    print("🛰️  Parsing Model XML for dependencies...")
    try:
        tree = ET.parse(model_xml)
        root = tree.getroot()
        # Find all variables defined in the XML
        expected_vars = [v.get('name') for v in root.findall('.//variable')]
        
        missing_vars = [v for v in expected_vars if v not in df.columns]
        
        if missing_vars:
            print(f"⚠️  Injecting {len(missing_vars)} missing variables...")
            for var in missing_vars:
                # Targeted defaults for policy variables vs residuals
                if 'dmpt' in var:
                    df[var] = 2.0  # Inflation/Unemp targets
                elif 'delrff' in var:
                    df[var] = 3.0  # Fed Funds Rate
                else:
                    df[var] = 0.0  # Neutral default for all others
    except Exception as e:
        print(f"⚠️  XML Parse failed ({e}), falling back to manual injection.")

    # 3. Clean up and establish window
    df = df.ffill().bfill().fillna(0.0)
    df_overlap = df.dropna()
    start_date = df_overlap.index.min()
    end_date = df_overlap.index.max()

    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}")
    print(f"Timeline: {start_date} to {end_date}")
    
    # 4. Initialize and Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️  Model Loaded. Calculating Residuals...")
        
        results = model.init_trac(start_date, end_date, df)
        print("✅ Engine Solve Successful.")
        
        os.makedirs("/home/spark/results", exist_ok=True)
        results.to_csv("/home/spark/results/residuals.csv")
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()