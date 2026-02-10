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
    
    # Build initial DF
    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. XML-Aware Scraper (Targeting <name> tags revealed in Build 225)
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract content between <name> and </name> tags
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            
            # Filter for unique, valid variable names (lowercase)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            
            # MANDATORY POLICY BLOCKERS (Safety net)
            blockers = ['dmptmax', 'delrff', 'dmptmin', 'mptmax', 'mptmin', 'drff']
            for b in blockers:
                if b not in expected_vars:
                    expected_vars.append(b)

            # Identify what we are missing from the CSVs
            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"🛰️  Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} missing series...")
                
                # Bulk create missing columns to prevent fragmentation warnings
                new_cols = {}
                for var in missing_vars:
                    val = 2.0 if any(x in var for x in ['mpt', 'lur', 'pi']) else 0.0
                    new_cols[var] = val
                
                # Add all at once
                df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)
                
        except Exception as e:
            print(f"❌ Scraper Failed: {e}")

    # 3. Data Integrity
    df = df.ffill().bfill().fillna(0.0)
    print(f"📊 Final Matrix Shape: {df.shape}")

    # 4. Solve
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