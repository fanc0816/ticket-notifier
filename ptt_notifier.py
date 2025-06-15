import os
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from flask import Flask
import threading

app = Flask(__name__)

# =========＝ 基本設定 ＝＝＝＝
KEYWORDS       = ["理想混蛋"]
PAGES_TO_CHECK = 3            # 往前抓幾頁（含 index.html）
BOARD          = "Drama-Ticket"
CHECK_INTERVAL = 60           # 每 min 重新檢查一次

# 建議用環境變數，不要把 Token 寫死在程式裡
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID        = os.getenv("TG_CHAT_ID")
API_URL        = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# =========＝ requests Session ＋ Retry ＝＝＝＝
session = requests.Session()
session.cookies.update({"over18": "1"})               # 帶 age‑check
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
})
# 自動重試 3 次，500/502/503/504 都會重試
retries = Retry(total=3, backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

notified_links: set[str] = set()

def send_telegram_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❗️ 尚未設定 Telegram Token / Chat ID，略過推播")
        return
    try:
        session.post(API_URL, data={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as exc:
        print(f"⚠️ Telegram 傳送訊息失敗: {exc}")

# =========＝ 抓取文章 ＝＝＝＝
def fetch_articles() -> list[tuple[str, str]]:
    """
    回傳 [(title, full_url), ...]
    """
    base_url = "https://www.ptt.cc"
    articles = []

    for i in range(PAGES_TO_CHECK):
        # PTT 的頁碼規則：index.html, index1.html, index2.html ...
        page_path = "index.html" if i == 0 else f"index{i}.html"
        url = f"{base_url}/bbs/{BOARD}/{page_path}"

        try:
            res = session.get(url, timeout=10)
            res.raise_for_status()
        except Exception as exc:
            print(f"⚠️ 無法讀取 {url}：{exc}")
            continue

        soup   = BeautifulSoup(res.text, "html.parser")
        titles = soup.select("div.title a")

        for t in titles:
            title = t.text.strip()
            href  = t["href"]
            full  = base_url + href
            if any(k in title for k in KEYWORDS):
                articles.append((title, full))

        # 避免爬太快
        time.sleep(0.3)

    return articles

# =========＝ 定期執行 ＝＝＝＝
def crawler_loop() -> None:
    print("🚀 開始監控 PTT 票券板…")
    articles = fetch_articles()
    for title, link in articles:
        if link not in notified_links:
            notified_links.add(link)
            print(f"📢 {title}\n🔗 {link}\n")
            send_telegram_message(f"🎫 {title}\n🔗 {link}")

    print(f"✅ 本輪檢查結束，{CHECK_INTERVAL} 秒後重試…\n")
    threading.Timer(CHECK_INTERVAL, crawler_loop).start()

# Gunicorn / Flask 開好後，也要確保爬蟲執行
threading.Thread(target=crawler_loop, daemon=True).start()

# =========＝ Flask ＝＝＝＝
@app.route("/")
def home():
    return "PTT Ticket Notifier is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
