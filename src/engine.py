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

    # 2. DYNAMIC INJECTION: Handle XML Namespaces
    print("🛰️  Parsing Model XML for dependencies...")
    try:
        tree = ET.parse(model_xml)
        root = tree.getroot()
        
        # Use findall with wildcard to ignore namespaces (requires Python 3.8+)
        # Or manually strip namespaces if necessary
        expected_vars = []
        for elem in root.iter():
            # Check for the local name regardless of the URI prefix
            tag_local_name = elem.tag.split('}')[-1] 
            if tag_local_name == 'variable':
                name = elem.get('name')
                if name:
                    expected_vars.append(name)
        
        expected_vars = list(set(expected_vars))
        missing_vars = [v for v in expected_vars if v not in df.columns]
        
        if missing_vars:
            print(f"⚠️  Injecting {len(missing_vars)} missing variables into DataFrame...")
            for var in missing_vars:
                if 'dmpt' in var:
                    df[var] = 2.0
                elif 'delrff' in var:
                    df[var] = 3.0
                else:
                    df[var] = 0.0
        else:
            print("🧐 No missing variables detected in XML. Check XML structure.")

    except Exception as e:
        print(f"❌ Critical XML Parse Error: {e}")

    # 3. Data Cleaning
    df = df.ffill().bfill().fillna(0.0)
    start_date = df.index.min()
    end_date = df.index.max()

    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}") # Expecting (29, 300+)
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