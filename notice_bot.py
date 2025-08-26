import os
import requests
from bs4 import BeautifulSoup

URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def fetch_latest_notice():
    res = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 실제 HTML 구조에 맞춰 CSS 선택자 작성
    first_post = soup.select_one(".view-list ul li a")  # 필요시 구조 확인 후 수정
    if not first_post:
        raise Exception("공지사항 항목을 찾을 수 없습니다. CSS 선택자를 다시 확인하세요.")

    title = first_post.get_text(strip=True)
    link = first_post.get("href")
    if not link.startswith("http"):
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
