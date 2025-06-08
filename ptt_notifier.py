import requests
from bs4 import BeautifulSoup
import threading
from flask import Flask
import os

app = Flask(__name__)

KEYWORDS = ["理想混蛋"]
PAGES = 3
BOARD = "Drama-Ticket"
CHECK_INTERVAL = 60  # 秒

TELEGRAM_TOKEN = "8130782294:AAHoPu2Po5TdP7oB6ztAj5Y6SwzFciNvcOU"
CHAT_ID = "8094404595"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

notified_links = set()

def send_telegram_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    try:
        requests.post(API_URL, data=payload)
    except Exception as e:
        print(f"⚠️ Telegram 傳送訊息失敗: {e}")

def fetch_articles():
    base_url = "https://www.ptt.cc"
    matched = []
    for page in range(PAGES):
        page_url = f"{base_url}/bbs/{BOARD}/index.html" if page == 0 else f"{base_url}/bbs/{BOARD}/index{page+1}.html"
        try:
            res = requests.get(page_url, cookies={"over18": "1"})
            soup = BeautifulSoup(res.text, "html.parser")
            titles = soup.select("div.title a")
            for title in titles:
                text = title.text.strip()
                href = title["href"]
                full_url = base_url + href
                if any(keyword in text for keyword in KEYWORDS):
                    matched.append((text, full_url))
        except Exception as e:
            print(f"⚠️ 無法讀取 {page_url}：{e}")
    return matched

def crawler_loop():
    print("🚀 開始監控 PTT 演唱會票...")
    new_articles = fetch_articles()
    for title, link in new_articles:
        if link not in notified_links:
            notified_links.add(link)
            print(f"📢 新文章：{title}")
            print(f"🔗 {link}\n")
            send_telegram_message(f"🎫 {title}\n🔗 {link}")
    print(f"⏳ {CHECK_INTERVAL} 秒後再次檢查...\n")
    threading.Timer(CHECK_INTERVAL, crawler_loop).start()

# **把爬蟲執行緒放在全域，確保Gunicorn啟動也會執行**
threading.Thread(target=crawler_loop, daemon=True).start()

@app.route("/")
def home():
    return "PTT Ticket Notifier is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
