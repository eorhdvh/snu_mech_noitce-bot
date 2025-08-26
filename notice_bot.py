import os
import requests
from bs4 import BeautifulSoup

URL = "https://me.snu.ac.kr/ko/board/notice"  # 서울대 기계공학부 공지사항
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")  # GitHub Secrets에서 불러오기

def fetch_latest_notice():
    res = requests.get(URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    # 공지사항 첫 번째 글의 제목과 링크 (CSS 선택자는 실제 사이트에 맞춰야 함)
    first_post = soup.select_one(".view-content .views-row a")
    title = first_post.text.strip()
    link = "https://me.snu.ac.kr" + first_post.get("href")
    return title, link

def send_to_discord(title, link):
    data = {
        "content": f"새로운 공지사항: **{title}**\n{link}"
    }
    requests.post(WEBHOOK_URL, json=data)

if __name__ == "__main__":
    try:
        title, link = fetch_latest_notice()
        send_to_discord(title, link)
        print(f"전송됨: {title}")
    except Exception as e:
        print("오류 발생:", e)
