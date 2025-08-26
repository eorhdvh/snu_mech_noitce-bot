import os
import requests
from bs4 import BeautifulSoup

URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"  # 기계공학부 공지사항 페이지
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")  # GitHub Secrets로부터 불러오기

def fetch_latest_notice():
    res = requests.get(URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 공지사항 첫 번째 항목의 제목과 링크 가져오기
    first_post = soup.select_one("table tbody tr td.title a")  # ← 올바른 선택자
    if not first_post:
        raise Exception("공지사항 항목을 찾을 수 없습니다. CSS 선택자를 다시 확인하세요.")

    title = first_post.text.strip()
    link = "https://me.snu.ac.kr" + first_post.get("href")  # 상대경로 → 절대경로로 변환
    return title, link

def send_to_discord(title, link):
    data = {
        "content": f"새로운 공지사항: **{title}**\n{link}"
    }
    response = requests.post(WEBHOOK_URL, json=data)
    print("디스코드 응답 코드:", response.status_code)
    print("응답 내용:", response.text)

if __name__ == "__main__":
    try:
        title, link = fetch_latest_notice()
        print("크롤링 결과:", title, link)  # 디버그용
        send_to_discord(title, link)
    except Exception as e:
        print("오류 발생:", e)
