import os
import requests
import pandas as pd
import urllib3

# Suppress insecure request warnings for the verify=False hack
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set',
    })

    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        # verify=False helps if the Docker container lacks updated CA certificates
        r = session.get(excel_url, timeout=30, verify=False)
        
        if r.status_code == 200 and (r.content.startswith(b'PK') or 'spreadsheet' in r.headers.get('Content-Type', '')):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ CSV Generated: {output_csv}")
        else:
            print(f"❌ Blocked. Received: {r.headers.get('Content-Type')}")
            # If still blocked, we might need to proxy or use a headless browser
    except Exception as e:
        print(f"❌ Fetch Error: {e}")

if __name__ == "__main__":
    fetch_tealbook_data()