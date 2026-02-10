import pandas as pd
import os
import re
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    
    # 1. Load merged CSVs
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))
    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. DYNAMIC INJECTION with Path Validation
    print(f"🧐 Checking for XML at: {model_xml}")
    if os.path.exists(model_xml):
        print("✅ XML File exists. Attempting read...")
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Improved Regex: Captures name="VAR" or name='VAR' or name=VAR
            found_vars = re.findall(r'name=["\']?(\w+)["\']?', xml_content)
            expected_vars = list(set(found_vars))
            
            missing_vars = [v for v in expected_vars if v not in df.columns]
            print(f"🛰️  Found {len(expected_vars)} potential variables in XML.")
            
            if missing_vars:
                print(f"⚠️  Injecting {len(missing_vars)} missing variables...")
                for var in missing_vars:
                    if 'dmpt' in var: df[var] = 2.0
                    elif 'delrff' in var: df[var] = 3.0
                    else: df[var] = 0.0
        except Exception as e:
            print(f"❌ Could not read XML file: {e}")
    else:
        print(f"🚨 XML FILE NOT FOUND! Check 'docker cp' stage.")

    # 3. Final Prep
    df = df.ffill().bfill().fillna(0.0)
    
    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}") 
    print(f"Variables present: {list(df.columns[:5])} ... {list(df.columns[-5:])}")
    
    # 4. Initialize and Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️  Model Loaded. Calculating Residuals...")
        results = model.init_trac(df.index.min(), df.index.max(), df)
        print("✅ Engine Solve Successful.")
        
        os.makedirs("/home/spark/results", exist_ok=True)
        results.to_csv("/home/spark/results/residuals.csv")
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()