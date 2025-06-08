import requests
from bs4 import BeautifulSoup
import time

# 設定區
KEYWORDS = ["理想混蛋", "演唱會", "門票"]
PAGES = 3  # 要爬的頁數
BOARD = "Drama-Ticket"
CHECK_INTERVAL = 300  # 每幾秒檢查一次（例如 300 秒 = 5 分鐘）

# Telegram 設定
TELEGRAM_TOKEN = "8130782294:AAHoPu2Po5TdP7oB6ztAj5Y6SwzFciNvcOU"
CHAT_ID = "8094404595"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# 儲存已通知過的文章
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

def main_loop():
    print("🚀 開始監控 PTT 演唱會票...")
    while True:
        new_articles = fetch_articles()
        for title, link in new_articles:
            if link not in notified_links:
                notified_links.add(link)
                print(f"📢 新文章：{title}")
                send_telegram_message(f"🎫 {title}\n🔗 {link}")
        print(f"⏳ 等待 {CHECK_INTERVAL} 秒後再次檢查...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()