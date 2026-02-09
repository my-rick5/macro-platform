import os
import requests
import pandas as pd
import urllib3

# Suppress SSL warnings for the verify=False workaround
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Use a session to persist cookies and headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set',
        'Connection': 'keep-alive'
    })

    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        # Step 1: Establish a real session by hitting the landing page
        session.get("https://www.philadelphiafed.org/", timeout=15, verify=False)
        
        # Step 2: Download the file
        r = session.get(excel_url, timeout=30, verify=False)
        
        # Check for the 'PK' zip header (standard for .xlsx files)
        if r.status_code == 200 and r.content.startswith(b'PK'):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ CSV Generated: {output_csv}")
        else:
            print(f"❌ Blocked. Received Content-Type: {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"❌ Fetch Error: {e}")

if __name__ == "__main__":
    fetch_tealbook_data()