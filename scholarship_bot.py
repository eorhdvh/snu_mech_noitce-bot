import os
import requests
from bs4 import BeautifulSoup

# 1. 크롤링할 목표 URL (장학 공지사항으로 변경)
URL = "https://me.snu.ac.kr/장학-공지사항/"

# 스크립트가 위치한 디렉토리 경로를 얻어 파일을 저장할 위치를 지정합니다.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 파일명을 변경하여 기존 학부 공지와 섞이지 않게 관리합니다.
LAST_NOTICE_FILE = os.path.join(SCRIPT_DIR, "last_scholarship_notice.txt")

def fetch_latest_notice():
    """
    웹사이트에서 가장 최신 공지사항의 제목과 링크를 가져옵니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    # verify=False는 SSL 인증서 오류 발생 시에만 사용하세요. (서울대 사이트는 종종 필요할 때가 있음)
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 기계과 홈페이지 구조상 장학 게시판도 동일한 CSS Selector를 사용할 확률이 높습니다.
    first_post_link = soup.select_one("ul.board_body li:nth-child(1) a")
    
    if not first_post_link:
        raise Exception("최신 공지사항 항목을 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")

    title = first_post_link.get_text(strip=True)
    link = first_post_link.get("href")
    
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
        
    return title, link

def send_to_discord(title, link):
    """
    디스코드 웹훅으로 새로운 공지사항 알림을 보냅니다.
    """
    WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
    
    if not WEBHOOK_URL:
        print("🔔 알림: DISCORD_WEBHOOK 환경 변수가 설정되지 않아 메시지를 보내지 않습니다.")
        return
        
    data = {
        # 3. 메시지 내용을 장학 공지에 맞게 수정
        "content": f"💰 **서울대 기계과 [장학] 새 공지!**\n\n**{title}**\n{link}"
    }
    
    response = requests.post(WEBHOOK_URL, json=data)
    
    if response.status_code >= 400:
        print(f"❌ 디스코드 메시지 전송 실패: {response.status_code}, 응답: {response.text}")
    else:
        print(f"✅ 디스코드 메시지 전송 성공: {title}")

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # 이전에 저장된 장학 공지 제목을 읽어옵니다.
    try:
        with open(LAST_NOTICE_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
    except FileNotFoundError:
        last_title = ""

    try:
        latest_title, latest_link = fetch_latest_notice()
        print("✅ 장학 공지 크롤링 성공!")
        print(f"   - 현재 최신 제목: {latest_title}")
        print(f"   - 이전에 보낸 제목: {last_title if last_title else '없음'}")

        if latest_title != last_title:
            print("🚀 새로운 장학 공지를 발견했습니다! 알림을 보냅니다.")
            send_to_discord(latest_title, latest_link)
            
            # 알림을 보낸 경우에만 파일을 업데이트하는 것이 안전할 수 있으나,
            # 여기서는 로직 유지를 위해 항상 업데이트합니다.
            with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                f.write(latest_title)
        else:
            print("✅ 새로운 장학 공지가 없습니다.")
            # 파일이 없으면 생성해두기 위해 작성
            if not os.path.exists(LAST_NOTICE_FILE):
                 with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                    f.write(latest_title)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
