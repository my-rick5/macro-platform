import os
import requests
import pandas as pd

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Use a session to persist headers and cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        # First, hit the base domain to get a session cookie
        session.get("https://www.philadelphiafed.org/", timeout=10)
        
        r = session.get(excel_url, timeout=30)
        if r.status_code == 200 and 'application' in r.headers.get('Content-Type', ''):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ CSV Generated: {output_csv}")
        else:
            print(f"❌ Blocked. Content-Type: {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"❌ Fetch Error: {e}")

if __name__ == "__main__":
    fetch_tealbook_data()