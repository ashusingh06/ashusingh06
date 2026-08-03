import json
import requests
from bs4 import BeautifulSoup

USERNAME = "ashusingh06"

url = f"https://github.com/users/{USERNAME}/contributions"

response = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

if response.status_code != 200:
    raise SystemExit(f"Failed ({response.status_code})")

html = response.text

# Save HTML
with open("data/contributions.html", "w", encoding="utf-8") as f:
    f.write(html)

soup = BeautifulSoup(html, "html.parser")

days = []

for rect in soup.select("td[data-date]"):
    days.append({
        "date": rect["data-date"],
        "count": int(rect.get("data-count", 0)),
        "level": int(rect.get("data-level", 0))
    })

with open("data/contributions.json", "w", encoding="utf-8") as f:
    json.dump(days, f, indent=2)

print(f"Saved {len(days)} contribution days.")
print("JSON -> data/contributions.json")