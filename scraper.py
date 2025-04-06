import requests
from bs4 import BeautifulSoup
from datetime import datetime, time, timezone
from supabase import create_client, Client

SUPABASE_URL = "https://wqkmdfgklgiczdqptidb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TABLE_NAME = "tracked_values"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ASSETS = [
    {"name": "EUR/USD", "url": "https://www.ig.com/uk/forex/markets-forex/eur-usd", "group": "forex"},
    {"name": "GBP/USD", "url": "https://www.ig.com/uk/forex/markets-forex/gbp-usd", "group": "forex"},
    {"name": "USD/JPY", "url": "https://www.ig.com/uk/forex/markets-forex/usd-jpy", "group": "forex"},
    {"name": "USD/CNH", "url": "https://www.ig.com/uk/forex/markets-forex/usd-cnh", "group": "forex"},
    {"name": "Gold", "url": "https://www.ig.com/uk/commodities/markets-commodities/gold", "group": "forex"},
    {"name": "Crude Oil", "url": "https://www.ig.com/uk/commodities/markets-commodities/us-light-crude", "group": "forex"},
    {"name": "FTSE 100", "url": "https://www.ig.com/uk/indices/markets-indices/ftse-100", "group": "uk"},
    {"name": "Germany 40", "url": "https://www.ig.com/uk/indices/markets-indices/germany-40", "group": "germany"},
    {"name": "EU Stocks 50", "url": "https://www.ig.com/uk/indices/markets-indices/eu-stocks-50", "group": "europe"},
    {"name": "Japan 225", "url": "https://www.ig.com/uk/indices/markets-indices/japan-225", "group": "tokyo"},
    {"name": "Hong Kong HS", "url": "https://www.ig.com/uk/indices/markets-indices/hong-kong-hs42", "group": "hongkong"},
    {"name": "Wall Street", "url": "https://www.ig.com/uk/indices/markets-indices/wall-street", "group": "usa"},
]

MARKET_HOURS = {
    "forex": (time(0, 0), time(23, 59)),
    "uk": (time(8, 0), time(16, 30)),
    "germany": (time(8, 0), time(16, 30)),
    "europe": (time(8, 0), time(16, 30)),
    "tokyo": (time(0, 0), time(6, 0)),
    "hongkong": (time(1, 30), time(8, 0)),
    "usa": (time(13, 30), time(20, 0)),
}

def is_market_open(group):
    now = datetime.utcnow().time()
    start, end = MARKET_HOURS.get(group, (None, None))
    return start <= now <= end if start and end else False

def extract_buy_percentage(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    bar = soup.find("div", class_="price-ticket__long-bar")
    if not bar or "--long-percent" not in bar.get("style", ""):
        raise ValueError("Long percent not found")
    style = bar["style"]
    percent_str = style.split(":")[1].replace(";", "").replace("%", "").strip()
    return float(percent_str)

def log_to_supabase(name, buy):
    sell = round(100 - buy, 2)
    timestamp = datetime.now(timezone.utc).isoformat()
    data = {"asset_name": name, "buy": buy, "sell": sell, "timestamp": timestamp}
    res = supabase.table(TABLE_NAME).insert(data).execute()
    if res.data:
        print(f"✅ {name}: Buy={buy}%, Sell={sell}%, Time={timestamp}")
    else:
        print(f"❌ Supabase error inserting {name}: {res}")

for asset in ASSETS:
    try:
        if is_market_open(asset["group"]):
            buy = extract_buy_percentage(asset["url"])
            log_to_supabase(asset["name"], buy)
        else:
            print(f"⏳ Market closed for {asset['name']} — skipped.")
    except Exception as e:
        print(f"❌ Error scraping {asset['name']}: {e}")
