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

    # 2. Aggressive Dynamic Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # This regex looks for any alphanumeric string assigned to name, alias, or series 
            # It also handles potential whitespace or different quote types
            found_vars = re.findall(r'(?:name|alias|series)\s*=\s*["\']([^"\']+)["\']', xml_content)
            expected_vars = list(set(found_vars))
            
            print(f"🛰️  Scraper found {len(expected_vars)} unique identifiers in XML.")
            
            # Force-add dmptmax just in case the scraper still misses it
            if 'dmptmax' not in expected_vars:
                expected_vars.append('dmptmax')

            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"⚠️  Injecting {len(missing_vars)} missing series...")
                for var in missing_vars:
                    # Provide standard default values for FRB/US policy/threshold variables
                    if 'dmpt' in var: df[var] = 2.0
                    elif 'delrff' in var: df[var] = 3.0
                    else: df[var] = 0.0
        except Exception as e:
            print(f"❌ Scraper Error: {e}")
    
    # 3. Final Prep & Gap Filling
    df = df.ffill().bfill().fillna(0.0)
    
    print(f"\n📊 --- MASTER DATA MATRIX ---")
    print(f"Total Shape: {df.shape}") 
    
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