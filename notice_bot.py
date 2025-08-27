import os
import requests
from bs4 import BeautifulSoup

# 1. '학부 공지사항' 목록 페이지의 정확한 URL
URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
# 만약 DISCORD_WEBHOOK 환경 변수 설정 없이 테스트하려면 아래 주석을 해제하고 실제 웹훅 URL을 입력하세요.
# WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

def fetch_latest_notice():
    """웹사이트에서 가장 최신 공지사항의 제목과 링크를 가져옵니다."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()  # 요청이 실패하면 오류 발생
    soup = BeautifulSoup(res.text, "html.parser")

    # 2. '학부 공지사항' 페이지의 HTML 구조에 맞는 정확한 CSS 선택자
    # 공지사항 테이블(div.board_skin_list)의 첫 번째 게시글(tr)의 제목 칸(td.subject)에 있는 링크(a)를 선택
    first_post_link = soup.select_one("div.board_skin_list tbody tr td.subject a")
    
    if not first_post_link:
        raise Exception("최신 공지사항 항목을 찾을 수 없습니다. CSS 선택자를 다시 확인해야 합니다.")

    title = first_post_link.get_text(strip=True)
    link = first_post_link.get("href")
    
    # 링크가 상대 경로('/'로 시작)일 경우, 전체 URL로 만들어줍니다.
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
        
    return title, link

def send_to_discord(title, link):
    """디스코드 웹훅으로 새로운 공지사항 알림을 보냅니다."""
    if not WEBHOOK_URL or WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("알림: DISCORD_WEBHOOK_URL이 설정되지 않아 디스코드로 메시지를 보내지 않습니다.")
        return
        
    data = {"content": f"📢 서울대 기계과 학부 공지사항 알림\n\n**{title}**\n{link}"}
    response = requests.post(WEBHOOK_URL, json=data)
    
    if response.status_code >= 400:
        print(f"❌ 디스코드 메시지 전송 실패: {response.status_code}")
        print(f"   응답 내용: {response.text}")
    else:
        print("✅ 디스코드 메시지 전송 성공!")


if __name__ == "__main__":
    try:
        latest_title, latest_link = fetch_latest_notice()
        print("✅ 크롤링 성공!")
        print(f"   - 제목: {latest_title}")
        print(f"   - 링크: {latest_link}")
        send_to_discord(latest_title, latest_link)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
