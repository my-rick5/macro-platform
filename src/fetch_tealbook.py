import os
import requests
import pandas as pd

def fetch_tealbook_data():
    data_dir = "/home/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a session to handle cookies/state
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.philadelphiafed.org/'
    })

    excel_url = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
    local_xlsx = os.path.join(data_dir, "tealbook_raw.xlsx")
    output_csv = os.path.join(data_dir, "tealbook_unemployment.csv")
    
    print("📡 Fetching Excel Projections...")
    try:
        r = session.get(excel_url, timeout=30)
        # Check if we got an actual file (Excel files start with PK signature)
        if r.status_code == 200 and r.content.startswith(b'PK'):
            with open(local_xlsx, 'wb') as f:
                f.write(r.content)
            df = pd.read_excel(local_xlsx, sheet_name='RUC', engine='openpyxl')
            df.to_csv(output_csv, index=False)
            print(f"✅ CSV Generated at {output_csv}")
        else:
            print(f"❌ Blocked. Server returned: {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"❌ Fetch Failed: {e}")

if __name__ == "__main__":
    fetch_tealbook_data()