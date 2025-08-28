import os
import requests
from bs4 import BeautifulSoup

# 크롤링할 목표 URL
URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"

# 스크립트가 위치한 디렉토리 경로를 얻어 파일을 저장할 위치를 지정합니다.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_NOTICE_FILE = os.path.join(SCRIPT_DIR, "last_notice.txt")

def fetch_latest_notice():
    """
    웹사이트에서 가장 최신 공지사항의 제목과 링크를 가져옵니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

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
        "content": f"📢 서울대 기계과 새 공지!\n\n**{title}**\n{link}"
    }
    
    response = requests.post(WEBHOOK_URL, json=data)
    
    if response.status_code >= 400:
        print(f"❌ 디스코드 메시지 전송 실패: {response.status_code}, 응답: {response.text}")
    else:
        print("✅ 디스코드 메시지 전송 성공!")

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    # 1. 이전에 저장된 공지사항 제목을 읽어옵니다.
    try:
        with open(LAST_NOTICE_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
    except FileNotFoundError:
        # 파일이 없으면 (최초 실행 시) 빈 문자열로 처리합니다.
        last_title = ""

    try:
        # 2. 웹사이트에서 현재 최신 공지사항을 가져옵니다.
        latest_title, latest_link = fetch_latest_notice()
        print("✅ 크롤링 성공!")
        print(f"   - 현재 최신 제목: {latest_title}")
        print(f"   - 이전에 보낸 제목: {last_title if last_title else '없음'}")

        # 3. 이전 제목과 현재 제목을 비교합니다.
        if latest_title != last_title:
            # 4. 두 제목이 다르면, 새로운 공지사항으로 판단하고 알림을 보냅니다.
            print("🚀 새로운 공지사항을 발견했습니다! 알림을 보냅니다.")
            send_to_discord(latest_title, latest_link)
        else:
            # 5. 두 제목이 같으면, 아무것도 하지 않습니다.
            print("✅ 새로운 공지사항이 없습니다. 알림을 보내지 않습니다.")
        
        # 6. 알림 전송 여부와 상관없이 파일에 최신 제목을 덮어씁니다.
        #    이렇게 해야 다음 워크플로우 실행 시 아티팩트가 존재하게 됩니다.
        with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
            f.write(latest_title)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
