import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 1. 크롤링할 목표 URL (공통 공지사항)
# 한글 주소가 인코딩된 형태일 수 있으나, 파이썬 requests는 둘 다 잘 처리합니다.
URL = "https://me.snu.ac.kr/공통-공지사항/"

# 스크립트 위치 및 저장 파일 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_NOTICE_FILE = os.path.join(SCRIPT_DIR, "last_common_notice.txt")

def fetch_latest_notice_by_date():
    """
    공통 공지 게시판에서 모든 게시물을 가져온 뒤, 날짜순으로 정렬하여 
    가장 최신의 제목과 링크를 반환합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. 모든 게시물 리스트 가져오기
    post_items = soup.select("ul.board_body li")
    
    if not post_items:
        raise Exception("게시물 리스트를 찾을 수 없습니다. CSS Selector를 확인해주세요.")

    posts = []

    for item in post_items:
        # 제목 및 링크
        link_tag = item.select_one("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")
        
        if link and link.startswith("/"):
            link = "https://me.snu.ac.kr" + link

        # 2. 날짜 추출 (span.date 가정)
        date_tag = item.select_one("span.date") 
        post_date = "1900-01-01"
        
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                post_date = date_text.replace(".", "-")
            except:
                pass
        
        posts.append({
            "title": title,
            "link": link,
            "date": post_date
        })

    # 3. 날짜 기준 내림차순 정렬
    if not posts:
        raise Exception("유효한 게시물을 찾지 못했습니다.")

    posts.sort(key=lambda x: x["date"], reverse=True)

    # 가장 최신 글
    latest_post = posts[0]
    
    return latest_post["title"], latest_post["link"]

def send_to_discord(title, link):
    """
    디스코드 웹훅 전송
    """
    WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
    
    if not WEBHOOK_URL:
        print("🔔 알림: DISCORD_WEBHOOK 환경 변수가 설정되지 않아 메시지를 보내지 않습니다.")
        return
        
    data = {
        # [공통] 머리말 적용
        "content": f"📢 **서울대 기계과 [공통] 새 공지!**\n\n**{title}**\n{link}"
    }
    
    response = requests.post(WEBHOOK_URL, json=data)
    
    if response.status_code >= 400:
        print(f"❌ 디스코드 메시지 전송 실패: {response.status_code}, 응답: {response.text}")
    else:
        print(f"✅ 디스코드 메시지 전송 성공: {title}")

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    try:
        # 이전 제목 읽기
        try:
            with open(LAST_NOTICE_FILE, "r", encoding="utf-8") as f:
                last_title = f.read().strip()
        except FileNotFoundError:
            last_title = ""

        # 날짜 정렬 로직으로 최신글 가져오기
        latest_title, latest_link = fetch_latest_notice_by_date()
        
        print("✅ 공통 공지 크롤링 성공!")
        print(f"   - 감지된 최신 제목: {latest_title}")
        print(f"   - 이전에 보낸 제목: {last_title if last_title else '없음'}")

        if latest_title != last_title:
            print("🚀 새로운 공통 공지를 발견했습니다! 알림을 보냅니다.")
            send_to_discord(latest_title, latest_link)
            
            with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                f.write(latest_title)
        else:
            print("✅ 새로운 공통 공지가 없습니다.")
            if not os.path.exists(LAST_NOTICE_FILE):
                 with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                    f.write(latest_title)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
