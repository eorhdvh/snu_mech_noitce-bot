import os
import requests
from bs4 import BeautifulSoup

# 크롤링할 목표 URL (서울대 기계공학부 공통 공지사항)
URL = "https://me.snu.ac.kr/%ea%b3%b5%ed%86%b5-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"

def fetch_latest_notice():
    """
    웹사이트에서 가장 최신 공지사항의 제목과 링크를 가져옵니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()  # 요청 실패 시 오류 발생
    soup = BeautifulSoup(res.text, "html.parser")

    # 'board_body' 클래스를 가진 ul 안의 첫 번째 li 항목(게시글) 안에 있는 링크(a)를 선택
    first_post_link = soup.select_one("ul.board_body li:nth-child(1) a")
    
    if not first_post_link:
        raise Exception("최신 공지사항 항목을 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")

    # 링크 안의 텍스트가 여러 div로 나뉘어 있을 수 있으므로 .get_text() 사용
    title = first_post_link.get_text(strip=True)
    link = first_post_link.get("href")
    
    # 링크가 상대 경로일 경우, 전체 URL로 만들어줍니다.
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
        
    return title, link

def send_to_discord(title, link):
    """
    디스코드 웹훅으로 새로운 공지사항 알림을 보냅니다.
    """
    # GitHub Secrets 또는 로컬 환경 변수에서 웹훅 URL을 가져옵니다.
    WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
    
    # 웹훅 URL이 설정되지 않았으면 알림을 출력하고 함수를 종료합니다.
    if not WEBHOOK_URL:
        print("🔔 알림: DISCORD_WEBHOOK 환경 변수가 설정되지 않아 메시지를 보내지 않습니다.")
        return
        
    # 디스코드로 보낼 메시지 데이터 (JSON 형식)
    data = {
        "content": f"📢 서울대 기계과 새 공지!\n\n**{title}**\n{link}"
    }
    
    # POST 요청으로 메시지 전송
    response = requests.post(WEBHOOK_URL, json=data)
    
    # 전송 실패 시 오류 메시지 출력
    if response.status_code >= 400:
        print(f"❌ 디스코드 메시지 전송 실패: {response.status_code}")
        print(f"   응답 내용: {response.text}")
    else:
        print("✅ 디스코드 메시지 전송 성공!")

# 이 스크립트가 직접 실행될 때만 아래 코드를 실행
if __name__ == "__main__":
    try:
        latest_title, latest_link = fetch_latest_notice()
        print("✅ 크롤링 성공!")
        print(f"   - 제목: {latest_title}")
        print(f"   - 링크: {latest_link}")
        
        # 크롤링한 최신 공지사항 정보를 디스코드로 보냅니다.
        send_to_discord(latest_title, latest_link)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
