import pandas as pd
import os
import re
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

    # 2. DYNAMIC INJECTION: Regex Extraction (The "Nuclear" Option)
    print("🛰️  Extracting dependencies from XML via text scan...")
    try:
        with open(model_xml, 'r') as f:
            xml_content = f.read()
        
        # Look for name="..." inside any tag (captures all variable definitions)
        # Specifically targeting the name attribute which is standard for FRB/US XML
        found_vars = re.findall(r'name=["\'](.*?)["\']', xml_content)
        expected_vars = list(set(found_vars))
        
        missing_vars = [v for v in expected_vars if v not in df.columns]
        
        if missing_vars:
            print(f"⚠️  Injecting {len(missing_vars)} missing variables into DataFrame...")
            for var in missing_vars:
                # Prioritize dmptmax and policy vars with neutral defaults
                if 'dmpt' in var:
                    df[var] = 2.0
                elif 'delrff' in var:
                    df[var] = 3.0
                else:
                    df[var] = 0.0
    except Exception as e:
        print(f"❌ Extraction failed: {e}")

    # 3. Final Prep
    df = df.ffill().bfill().fillna(0.0)
    start_date = df.index.min()
    end_date = df.index.max()

    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}") # We want to see 300+ here!
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