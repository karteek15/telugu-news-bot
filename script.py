import requests
import feedparser
import os
import json
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIG =================

RSS_URL = "https://news.google.com/rss/search?q=site:thehindu.com&hl=en-IN&gl=IN&ceid=IN:en"
POSTED_FILE = "posted.json"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")
AI_KEY = os.getenv("AI_KEY")

# ================= LOAD POSTED ARTICLES =================

if os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "r") as f:
        posted_links = json.load(f)
else:
    posted_links = []

# ================= READ RSS =================

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    print("No news found")
    exit()

entry = feed.entries[0]

if entry.link in posted_links:
    print("Already posted this news")
    exit()

article_text = entry.title

# ================= AI SUMMARY (TELUGU) =================

prompt = f"""
ఈ వార్తను తెలుగులో సంక్షిప్తంగా రాయండి:

అవసరాలు:
- శీర్షిక (8 పదాల లోపు)
- 2–3 చిన్న వాక్యాలు
- సులభమైన తెలుగు
- కొత్త పదాలతో రాయాలి

వార్త:
{article_text}
"""

ai_response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    },
    timeout=30
)

response_json = ai_response.json()

if "choices" not in response_json:
    print("AI ERROR RESPONSE:")
    print(response_json)
    exit()

result = response_json["choices"][0]["message"]["content"]

lines = result.split("\n")
headline = lines[0].strip()
summary = "\n".join(lines[1:]).strip()

# ================= IMAGE CREATION =================

img = Image.new("RGB", (800, 800), color="#1c1c1c")
draw = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
except:
    font = ImageFont.load_default()

draw.text((40, 350), headline, fill="white", font=font)

image_path = "news.png"
img.save(image_path)

# ================= SEND TO TELEGRAM =================

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

with open(image_path, "rb") as photo:
    telegram_response = requests.post(
        telegram_url,
        data={
            "chat_id": CHANNEL,
            "caption": f"📰 {headline}\n\n{summary}\n\nSource: The Hindu"
        },
        files={"photo": photo}
    )

print("Telegram response:", telegram_response.status_code)

# ================= SAVE POSTED LINK =================

posted_links.append(entry.link)

with open(POSTED_FILE, "w") as f:
    json.dump(posted_links, f)

print("Posted successfully")
