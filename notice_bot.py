import os
import requests
from bs4 import BeautifulSoup

# 1. 올바른 공지사항 '목록' 페이지 주소로 변경
URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/" 
# WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK") # 실제 사용 시 주석 해제
# 테스트를 위해 임시 WEBHOOK_URL을 사용하거나, 아래 send_to_discord 함수 호출 부분을 주석 처리하세요.
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE" # 이 부분은 실제 웹훅 주소로 변경해야 합니다.

def fetch_latest_notice():
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118 Safari/537.36"}
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 2. 실제 페이지 구조에 맞는 CSS 선택자로 수정 (td.views-field-title -> td.subject)
    # 공지사항 목록의 첫 번째 게시글(tr)의 제목(td.subject) 안에 있는 링크(a)를 선택합니다.
    first_post = soup.select_one("div.board_skin_list tbody tr td.subject a")
    
    if not first_post:
        raise Exception("공지사항 항목을 찾을 수 없습니다. CSS 선택자를 재확인해주세요!")

    title = first_post.get_text(strip=True)
    link = first_post.get("href")
    
    # 상대 경로인 경우 전체 URL로 만들어줍니다.
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
        
    return title, link

def send_to_discord(title, link):
    if WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("알림: DISCORD_WEBHOOK_URL이 설정되지 않아 디스코드로 메시지를 보내지 않습니다.")
        return
        
    data = {"content": f"📢 새로운 공지사항: **{title}**\n{link}"}
    response = requests.post(WEBHOOK_URL, json=data)
    print("디스코드 응답 코드:", response.status_code)
    # print("응답 내용:", response.text) # 디버깅이 필요할 때 주석 해제

if __name__ == "__main__":
    try:
        title, link = fetch_latest_notice()
        print("✅ 크롤링 성공!")
        print(f"   - 제목: {title}")
        print(f"   - 링크: {link}")
        send_to_discord(title, link)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
