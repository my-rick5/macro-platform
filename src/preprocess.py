import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor...")
    if not os.path.exists(excel_path):
        print(f"❌ CRITICAL: Excel file not found at {excel_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    for sheet in xls.sheet_names:
        if sheet.lower() in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        print(f"🔎 Processing Sheet: {sheet}")
        # Read the sheet with no header to find where the data starts
        df_all = pd.read_excel(xls, sheet_name=sheet, header=None)
        
        # FIND THE HEADER: Look for the first row that contains a 'Q' or a Year > 1900
        header_idx = 0
        for i, row in df_all.iterrows():
            row_str = " ".join(row.astype(str))
            # Catching "2024Q1", "2024 Q1", or even "1995:1"
            if re.search(r'(19|20)\d{2}[ :\-]?Q?\d', row_str):
                header_idx = i
                print(f"   🎯 Found Header at Row {i}")
                break
        
        # Reload with the correct header
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=header_idx)
        
        # Clean column names (remove colons/spaces)
        df.columns = [str(c).strip().replace(':', '') for c in df.columns]
        
        # Identify date-like columns (Year+Quarter)
        date_cols = [c for c in df.columns if re.search(r'\d{4}Q\d', c)]
        
        if not date_cols:
            print(f"   ⚠️ No standard date columns found. Trying index-based recovery...")
            # Fallback: Many Greenbooks have 'Year' in column 0 and 'Quarter' in column 1
            if 'Year' in df.columns and ('Quarter' in df.columns or 'Q' in df.columns):
                df['date'] = df['Year'].astype(int).astype(str) + "Q" + df.iloc[:, 1].astype(int).astype(str)
                date_cols = ['date']
        
        if date_cols:
            # We want the last row (the most recent forecast/vintage)
            # Some files have 'Vintage' rows; we take the bottom-most data point
            latest_row = df.iloc[-1]
            
            # Identify the variable name (default to sheet name)
            var_name = 'LUR' if 'unemp' in sheet.lower() else sheet.upper()
            
            # Create a simple 2-column CSV: [date, value]
            # If date_cols is multiple (like 2024Q1, 2024Q2...), we transpose them
            if len(date_cols) > 1:
                final_df = latest_row[date_cols].reset_index()
                final_df.columns = ['date', var_name]
            else:
                final_df = df[['date', var_name]] if var_name in df.columns else df.iloc[:, [0, -1]]
            
            # Standardize and save
            try:
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ Saved {var_name}")
            except Exception as e:
                print(f"   ❌ Formatting error in {sheet}: {e}")

    print(f"🏁 Finished. Found {len(os.listdir(output_dir))} variables.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')