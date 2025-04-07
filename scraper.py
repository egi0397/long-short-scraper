import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
import pytz  # <--- questo mancava
import os

# 🔐 Supabase credentials da GitHub Actions
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TABLE_NAME = "tracked_values"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ASSETS = [
    {"name": "EUR/USD", "url": "https://www.ig.com/uk/forex/markets-forex/eur-usd"},
    {"name": "GBP/USD", "url": "https://www.ig.com/uk/forex/markets-forex/gbp-usd"},
    {"name": "USD/JPY", "url": "https://www.ig.com/uk/forex/markets-forex/usd-jpy"},
    {"name": "USD/CNH", "url": "https://www.ig.com/uk/forex/markets-forex/usd-cnh"},
    {"name": "Gold", "url": "https://www.ig.com/uk/commodities/markets-commodities/gold"},
    {"name": "Crude Oil", "url": "https://www.ig.com/uk/commodities/markets-commodities/us-light-crude"},
    {"name": "FTSE 100", "url": "https://www.ig.com/uk/indices/markets-indices/ftse-100"},
    {"name": "Germany 40", "url": "https://www.ig.com/uk/indices/markets-indices/germany-40"},
    {"name": "EU Stocks 50", "url": "https://www.ig.com/uk/indices/markets-indices/eu-stocks-50"},
    {"name": "Japan 225", "url": "https://www.ig.com/uk/indices/markets-indices/japan-225"},
    {"name": "Hong Kong HS", "url": "https://www.ig.com/uk/indices/markets-indices/hong-kong-hs42"},
    {"name": "Wall Street", "url": "https://www.ig.com/uk/indices/markets-indices/wall-street"},
    {"name": "USD/CAD", "url": "https://www.ig.com/uk/forex/markets-forex/usd-cad"},
    {"name": "GBP/JPY", "url": "https://www.ig.com/uk/forex/markets-forex/gbp-jpy"},
    {"name": "EUR/AUD", "url": "https://www.ig.com/uk/forex/markets-forex/eur-aud"},
    {"name": "AUD/USD", "url": "https://www.ig.com/uk/forex/markets-forex/aud-usd"},
    {"name": "NZD/USD", "url": "https://www.ig.com/uk/forex/markets-forex/nzd-usd"},
    {"name": "AUD/NZD", "url": "https://www.ig.com/uk/forex/markets-forex/aud-nzd"},
    {"name": "EUR/GBP", "url": "https://www.ig.com/uk/forex/markets-forex/eur-gbp"},
    {"name": "USD/CHF", "url": "https://www.ig.com/uk/forex/markets-forex/usd-chf"},
]

def is_market_open_24_5() -> bool:
    utc_now = datetime.utcnow()
    london_tz = pytz.timezone("Europe/London")
    london_now = utc_now.replace(tzinfo=pytz.utc).astimezone(london_tz)

    weekday = london_now.weekday()  # Monday = 0, Sunday = 6
    hour = london_now.hour

    if weekday == 6 and hour >= 22:
        return True  # Domenica dopo le 22 UK
    elif weekday in [0, 1, 2, 3]:
        return True  # Da lunedì a giovedì
    elif weekday == 4 and hour < 22:
        return True  # Venerdì prima delle 22 UK
    return False

def extract_buy_percentage(url: str) -> float:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    bar = soup.find("div", class_="price-ticket__long-bar")
    if not bar or "--long-percent" not in bar.get("style", ""):
        raise ValueError("Long percent not found")
    style = bar["style"]
    percent_str = style.split(":")[1].replace(";", "").replace("%", "").strip()
    return float(percent_str)

def log_to_supabase(name: str, buy: float):
    sell = round(100 - buy, 2)
    timestamp = datetime.utcnow().isoformat()

    data = {
        "asset_name": name,
        "buy": buy,
        "sell": sell,
        "timestamp": timestamp
    }

    res = supabase.table(TABLE_NAME).insert(data).execute()
    if res.data:
        print(f"✅ {name}: Buy={buy}%, Sell={sell}%, Time={timestamp}")
    else:
        print(f"❌ Supabase error inserting {name}: {res}")

# MAIN
if is_market_open_24_5():
    for asset in ASSETS:
        try:
            buy = extract_buy_percentage(asset["url"])
            log_to_supabase(asset["name"], buy)
        except Exception as e:
            print(f"❌ Error scraping {asset['name']}: {e}")
else:
    print("⏳ Market closed (outside 24/5 range) — skipping all assets.")
