import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 크롤링할 목표 URL
URL = "https://me.snu.ac.kr/%ed%95%99%eb%b6%80-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"

# 스크립트 위치 및 저장 파일 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_NOTICE_FILE = os.path.join(SCRIPT_DIR, "last_notice.txt")

def fetch_latest_notice_by_date():
    """
    웹사이트의 게시물 목록을 모두 가져온 뒤, 날짜순으로 정렬하여 
    가장 최신의 제목과 링크를 반환합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. 모든 게시물 리스트를 가져옵니다. (기존 select_one -> select 변경)
    post_items = soup.select("ul.board_body li")
    
    if not post_items:
        raise Exception("게시물 리스트를 찾을 수 없습니다. CSS Selector를 확인해주세요.")

    posts = []

    for item in post_items:
        # 제목 및 링크 추출
        link_tag = item.select_one("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")
        
        # 링크 보정
        if link and link.startswith("/"):
            link = "https://me.snu.ac.kr" + link

        # 2. 날짜 추출 (중요: 실제 사이트의 날짜 태그 클래스명을 확인해야 합니다)
        # 보통 span.date, span.reg_date, div.date 등의 이름을 가집니다.
        # 아래는 span 태그 안에 날짜가 있다고 가정하고 작성된 코드입니다.
        date_tag = item.select_one("span.date") 
        
        # 만약 date 태그가 없다면, 본문 텍스트에서 날짜 형식을 찾거나 
        # 날짜가 없는 게시물(배너 등)은 제외합니다.
        post_date = "1900-01-01" # 기본값 (날짜 못 찾을 경우 맨 뒤로 보냄)
        
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                # 날짜 형식이 '2023.10.25' 또는 '2023-10-25'라고 가정
                post_date = date_text.replace(".", "-")
            except:
                pass
        
        posts.append({
            "title": title,
            "link": link,
            "date": post_date
        })

    # 3. 날짜(date)를 기준으로 내림차순(최신순) 정렬합니다.
    # 날짜가 같을 경우를 대비해 원래 리스트의 순서(보통 위쪽이 최신)도 고려되도록 sort는 안정적입니다.
    if not posts:
        raise Exception("유효한 게시물을 찾지 못했습니다.")

    # 날짜 문자열 기준으로 정렬 (예: "2023-10-25" > "2023-10-24")
    posts.sort(key=lambda x: x["date"], reverse=True)

    # 가장 최신 글(첫 번째 요소) 선택
    latest_post = posts[0]
    
    return latest_post["title"], latest_post["link"]

def send_to_discord(title, link):
    """
    디스코드 웹훅 전송 함수 (기존과 동일)
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
    try:
        # 1. 이전 제목 읽기
        try:
            with open(LAST_NOTICE_FILE, "r", encoding="utf-8") as f:
                last_title = f.read().strip()
        except FileNotFoundError:
            last_title = ""

        # 2. 날짜순 정렬 후 최신 공지 가져오기
        latest_title, latest_link = fetch_latest_notice_by_date()
        
        print("✅ 크롤링 성공 (날짜 정렬 적용)")
        print(f"   - 감지된 최신 제목: {latest_title}")
        print(f"   - 이전에 보낸 제목: {last_title if last_title else '없음'}")

        # 3. 비교 및 알림
        if latest_title != last_title:
            print("🚀 새로운 공지사항을 발견했습니다! 알림을 보냅니다.")
            send_to_discord(latest_title, latest_link)
            
            # 파일 업데이트
            with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                f.write(latest_title)
        else:
            print("✅ 새로운 공지사항이 없습니다.")
            
            # 파일이 없으면 생성 (안전장치)
            if not os.path.exists(LAST_NOTICE_FILE):
                with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                    f.write(latest_title)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
