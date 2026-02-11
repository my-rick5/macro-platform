import pandas as pd
import os
import sys

def run_pro_engine():
    print("🚀 Heartbeat: Production Macro Engine (Build #547-Lite-Compatible)")
    
    # 1. Environment & Path Setup
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Check for pyfrbus dependency
    try:
        from pyfrbus import frbus
        print("✅ FRB/US Solver Dependencies Loaded.")
    except Exception as e:
        print(f"❌ FATAL: Dependency Load Error: {e}")
        sys.exit(1)

    # 2. Data Loading (Based on Build #547's stable ingestion)
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found in data/processed")
        return

    df_list = []
    for f in files:
        temp_df = pd.read_csv(os.path.join(data_path, f))
        temp_df['date'] = pd.PeriodIndex(temp_df['date'], freq='Q')
        temp_df.set_index('date', inplace=True)
        df_list.append(temp_df)
    
    df = pd.concat(df_list, axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 3. Model Solver Execution
    model = frbus.Frbus(model_xml)
    solve_start = df.index.min() + 1
    solve_end = df.index.max()
    
    print(f"📈 Solving from {solve_start} to {solve_end}...")
    final_results = model.init_trac(solve_start, solve_end, df)

    # 4. Final Exports
    # --- Full Export ---
    full_path = os.path.join(results_dir, "residuals.csv")
    final_results.to_csv(full_path)
    print(f"✅ Full residuals saved to {full_path}")

    # --- Lite Export (Core Macro Variables) ---
    lite_path = os.path.join(results_dir, "residuals_lite.csv")
    lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
    
    # Safety check: only export variables that successfully solved
    available_vars = [v for v in lite_vars if v in final_results.columns]
    final_results[available_vars].to_csv(lite_path)
    print(f"✅ Lite residuals ({len(available_vars)} vars) saved to {lite_path}")

if __name__ == "__main__":
    run_pro_engine()