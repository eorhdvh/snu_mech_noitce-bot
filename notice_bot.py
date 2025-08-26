import os
import requests
from bs4 import BeautifulSoup

URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"  # 올바른 URL
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def fetch_latest_notice():
    # User-Agent 포함해서 요청 차단 회피
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118 Safari/537.36"}
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 첫 번째 공지사항 링크 선택
    first_post = soup.select_one("table.views-table tbody tr td.views-field-title a")
    if not first_post:
        raise Exception("공지사항 항목을 찾을 수 없습니다. CSS 선택자 재확인 필요!")

    title = first_post.get_text(strip=True)
    link = first_post.get("href")
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
    return title, link

def send_to_discord(title, link):
    data = {"content": f"새로운 공지사항: **{title}**\n{link}"}
    response = requests.post(WEBHOOK_URL, json=data)
    print("디스코드 응답 코드:", response.status_code)
    print("응답 내용:", response.text)

if __name__ == "__main__":
    try:
        title, link = fetch_latest_notice()
        print("크롤링 결과:", title, link)
        send_to_discord(title, link)
    except Exception as e:
        print("오류 발생:", e)
