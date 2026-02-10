import pandas as pd
import os
import re

def clean_fed_excel(excel_path, output_dir):
    print(f"🎬 Starting Preprocessor...")
    os.makedirs(output_dir, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    
    for sheet in xls.sheet_names:
        if sheet.lower() in ['documentation', 'notes', 'summary', 'definitions']:
            continue
            
        print(f"🔎 Processing Sheet: {sheet}")
        df = pd.read_excel(xls, sheet_name=sheet, skiprows=1)
        if df.empty: continue

        # 1. First column is our Date
        df.rename(columns={df.columns[0]: 'date'}, inplace=True)
        
        # 2. Variable Name Mapping
        var_name = 'LUR' if 'unemp' in sheet.lower() else sheet.upper()
        
        # 3. Date Standardization (Handle 1967:Q1 etc)
        def standardize_date(val):
            s = str(val).strip()
            s = re.sub(r'[:.\- ]', 'Q', s)
            match = re.search(r'(\d{4})Q(\d)', s)
            return f"{match.group(1)}Q{match.group(2)}" if match else None

        df['date'] = df['date'].apply(standardize_date)
        df = df.dropna(subset=['date'])

        # 4. DATA PICKER: Find the last column that is actually numeric
        # This avoids accidentally grabbing a 'Vintage Date' column at the end
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            # We take the latest (right-most) numeric column
            target_col = numeric_cols[-1]
            final_df = df[['date', target_col]].copy()
            final_df.columns = ['date', var_name]
            
            # 5. Filter out impossible values (like the date-integers we saw)
            # Growth rates and unemployment are rarely > 100 or < -100
            final_df = final_df[final_df[var_name].abs() < 1000]

            try:
                final_df['date'] = pd.PeriodIndex(final_df['date'], freq='Q')
                save_path = os.path.join(output_dir, f"{var_name.lower()}.csv")
                final_df.set_index('date').sort_index().to_csv(save_path)
                print(f"   ✅ Saved {var_name} ({len(final_df)} obs) - Sample: {final_df[var_name].iloc[-1]}")
            except Exception as e:
                print(f"   ❌ Formatting error: {e}")

    print(f"🏁 Finished. Found {len(os.listdir(output_dir))} variables.")

if __name__ == "__main__":
    clean_fed_excel('/home/spark/data/library.xlsx', '/home/spark/data/processed')