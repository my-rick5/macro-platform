import os
import requests
import pandas as pd

def fetch_tealbook_data():
    # URL for the Philadelphia Fed's main Tealbook Excel dataset
    # This URL is the permanent link for their consolidated Excel file
    data_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    local_path = os.path.join(data_dir, "tealbook_raw.xlsx")
    
    print(f"📡 Downloading Tealbook data from Philadelphia Fed...")
    response = requests.get(data_url)
    
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Download complete: {local_path}")
        
        # Simple extraction logic: Convert the first data sheet to CSV for the engine
        # In the Phil Fed file, sheets are named after variables (e.g., 'COREPCE', 'RUC')
        # For now, let's grab the Unemployment (RUC) sheet as a sample
        try:
            df = pd.read_excel(local_path, sheet_name='RUC')
            output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
            df.to_csv(output_csv, index=False)
            print(f"📝 Extracted Unemployment projections to {output_csv}")
        except Exception as e:
            print(f"⚠️ Could not extract specific sheet: {e}")
    else:
        print(f"❌ Failed to download data. Status code: {response.status_code}")

if __name__ == "__main__":
    fetch_tealbook_data()