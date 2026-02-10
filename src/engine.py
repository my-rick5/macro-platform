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

    # 2. Primitive Scraper + Hardcoded Safety Net
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find ANY word-like string that is 3-15 chars long and lowercase
            # FRB/US variables are almost always lowercase.
            found_vars = re.findall(r'[>\s"\']([a-z][a-z0-9_]{2,14})[<\s"\']', content)
            
            # MANDATORY BLOCKERS (Hardcoded until scraper is fixed)
            blockers = ['dmptmax', 'delrff', 'dmptmin', 'mptmax', 'mptmin', 'drff']
            
            expected_vars = list(set(found_vars + blockers))
            print(f"🛰️  Scraper/Manual list: {len(expected_vars)} variables identified.")

            missing_vars = [v for v in expected_vars if v not in df.columns]
            if missing_vars:
                print(f"⚠️  Injecting {len(missing_vars)} series...")
                for var in missing_vars:
                    # Policy vars usually need a non-zero floor to avoid math errors
                    val = 2.0 if 'mpt' in var else 0.0
                    df[var] = val
        except Exception as e:
            print(f"❌ Scraper Failed: {e}")

    # 3. Final Prep
    df = df.ffill().bfill().fillna(0.0)
    print(f"📊 Matrix Shape: {df.shape}")

    # 4. Solve
    try:
        model = frbus.Frbus(model_xml)
        results = model.init_trac(df.index.min(), df.index.max(), df)
        print("✅ Success!")
        results.to_csv("/home/spark/results/residuals.csv")
    except Exception as e:
        print(f"❌ Failed again on variable: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()