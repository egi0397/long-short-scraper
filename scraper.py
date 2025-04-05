import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = "https://wqkmdfgklgiczdqptidb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indxa21kZmdrbGdpY3pkcXB0aWRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NTEyNzgsImV4cCI6MjA1OTQyNzI3OH0.kHivXh-aErNsO-ktxwYf4hPl8Cl6leDNwGWzqG7xQ-g"
TABLE_NAME = "tracked_values"
URL = "https://www.ig.com/uk/indices/markets-indices/wall-street"  # Replace this with your target URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_value():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.select_one("div.price-ticket__long-bar")

    if not div:
        raise Exception("❌ Could not find the long/short bar on the page.")

    style = div.get("style")
    value_str = style.split(":")[1].strip().replace(";", "").replace("%", "")
    buy = float(value_str)
    sell = round(100.0 - buy, 2)

    print(f"📈 BUY (Long): {buy}% | 📉 SELL (Short): {sell}%")
    return buy, sell

def store_value(buy, sell):
    timestamp = datetime.now(timezone.utc).isoformat()
    data = {"timestamp": timestamp, "buy": buy, "sell": sell}
    response = supabase.table(TABLE_NAME).insert(data).execute()
    print("✅ Success! Inserted:", response)

if __name__ == "__main__":
    try:
        buy, sell = scrape_value()
        store_value(buy, sell)
    except Exception as e:
        print(f"❌ Error: {e}")