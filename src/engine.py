import pandas as pd
import os
import re
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load merged CSVs from Preprocessor
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ No processed data found in /home/spark/data/processed")
        return

    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))
    
    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. XML-Aware Scraper
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"🛰️  Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} missing series...")
                new_cols = {}
                for var in missing_vars:
                    val = 2.0 if any(x in var for x in ['mpt', 'lur', 'pi']) else 0.0
                    new_cols[var] = val
                
                df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Lag Padding & Data Integrity
    df = df.sort_index()
    start_date = df.index.min()
    padding_dates = [start_date - i for i in range(1, 5)]
    padding_df = pd.DataFrame(index=pd.PeriodIndex(padding_dates, freq='Q'), columns=df.columns)
    
    df = pd.concat([padding_df, df]).sort_index()
    df = df.ffill().bfill().fillna(0.0)
    
    # --- VERIFICATION LINE ---
    # This exports the exact matrix being sent to the FRB/US Solver
    verification_path = os.path.join(results_dir, "master_input_matrix.csv")
    df.to_csv(verification_path)
    print(f"💾 Verification file saved: {verification_path}")
    # -------------------------

    print(f"📊 Final Padded Matrix Shape: {df.shape}")

    # 4. Engine Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️  Model Loaded. Calculating Residuals...")
        
        # Start calculation from original start_date using the padded history
        results = model.init_trac(start_date, df.index.max(), df)
        
        print("✅ Engine Solve Successful.")
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()