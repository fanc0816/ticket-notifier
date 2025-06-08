import requests
from bs4 import BeautifulSoup
import time
import threading
from flask import Flask

app = Flask(__name__)

# 設定區
KEYWORDS = ["理想混蛋"]
PAGES = 3
BOARD = "Drama-Ticket"
CHECK_INTERVAL = 300  # 秒

# Telegram 設定
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
    requests.post(API_URL, data=payload)

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
    while True:
        new_articles = fetch_articles()
        for title, link in new_articles:
            if link not in notified_links:
                notified_links.add(link)
                print(f"📢 新文章：{title}")
                print(f"🔗 {link}\n")
                send_telegram_message(f"🎫 {title}\n🔗 {link}")
        print(f"⏳ 等待 {CHECK_INTERVAL} 秒後再次檢查...\n")
        time.sleep(CHECK_INTERVAL)

# 啟動背景爬蟲執行緒（daemon=True，不阻塞主程式）
threading.Thread(target=crawler_loop, daemon=True).start()

@app.route("/")
def home():
    return "PTT Ticket Notifier is running."

if __name__ == "__main__":
    # Railway 通常會用 PORT 環境變數，建議讀取設定
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
