import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
from supabase import create_client, Client

# 🔐 Supabase credentials
SUPABASE_URL = "https://wqkmdfgklgiczdqptidb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indxa21kZmdrbGdpY3pkcXB0aWRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NTEyNzgsImV4cCI6MjA1OTQyNzI3OH0.kHivXh-aErNsO-ktxwYf4hPl8Cl6leDNwGWzqG7xQ-g"

TABLE_NAME = "tracked_values"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🧠 Asset list
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

# ⏰ Market hours in UTC (escluso forex)
MARKET_HOURS = {
    "uk":        (time(8, 0), time(16, 30)),
    "germany":   (time(8, 0), time(16, 30)),
    "europe":    (time(8, 0), time(16, 30)),
    "tokyo":     (time(0, 0), time(6, 0)),
    "hongkong":  (time(1, 30), time(8, 0)),
    "usa":       (time(13, 30), time(20, 0)),
}

def is_market_open(group: str) -> bool:
    now = datetime.utcnow()
    weekday = now.weekday()  # Monday = 0, Sunday = 6

    if group == "forex":
        # Domenica 21:00 UTC a Venerdì 21:00 UTC (22:00 UK)
        if (weekday == 6 and now.time() >= time(21, 0)) or \
           (0 <= weekday <= 3) or \
           (weekday == 4 and now.time() <= time(21, 0)):
            return True
        else:
            return False
    else:
        start, end = MARKET_HOURS.get(group, (None, None))
        if start and end:
            return start <= now.time() <= end
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

# 🚀 MAIN LOOP
for asset in ASSETS:
    name = asset["name"]
    url = asset["url"]
    group = asset["group"]

    try:
        if is_market_open(group):
            buy = extract_buy_percentage(url)
            log_to_supabase(name, buy)
        else:
            print(f"⏳ Market closed for {name} — skipped.")
    except Exception as e:
        print(f"❌ Error scraping {name}: {e}")
