import pandas as pd
import numpy as np

def clean_residuals(input_file, output_file):
    df = pd.read_csv(input_file)
    
    # 1. Define "Lite" variables (standard FRB/US names)
    lite_vars = ['LUR', 'XGDP', 'PCE', 'RFF', 'CPI', 'date']
    
    # Keep only variables that actually exist in the file
    present_vars = [v for v in lite_vars if v in df.columns]
    lite_df = df[present_vars].copy()

    # 2. Cleanup: Remove rows where everything is NaN
    lite_df.dropna(how='all', inplace=True)

    # 3. Generate Descriptives
    print("\n--- 📊 LITE RESIDUAL SUMMARY ---")
    summary = lite_df.describe().T[['mean', 'std', 'min', 'max']]
    print(summary)
    
    # Check for mess (massive outliers or Inf values)
    if lite_df.isin([np.inf, -np.inf]).any().any():
        print("⚠️ WARNING: Infinite values detected in residuals!")

    lite_df.to_csv(output_file, index=False)
    print(f"\n✅ Lite version saved to: {output_file}")

if __name__ == "__main__":
    # Point this to your large calibration file
    clean_residuals('results/calibration_residuals_e.csv', 'results/lite_residuals.csv')
