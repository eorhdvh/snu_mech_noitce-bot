import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 1. 크롤링할 목표 URL (장학 공지사항)
URL = "https://me.snu.ac.kr/장학-공지사항/"

# 스크립트가 위치한 디렉토리 경로를 얻어 파일을 저장할 위치를 지정합니다.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 파일명을 변경하여 기존 학부 공지와 섞이지 않게 관리합니다.
LAST_NOTICE_FILE = os.path.join(SCRIPT_DIR, "last_scholarship_notice.txt")

def fetch_latest_notice_by_date():
    """
    장학 공지 게시판에서 모든 게시물을 가져온 뒤, 날짜순으로 정렬하여 
    가장 최신의 제목과 링크를 반환합니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    # verify=False는 SSL 인증서 오류 발생 시에만 사용하세요.
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. 모든 게시물 리스트를 가져옵니다. (nth-child(1) 제거)
    post_items = soup.select("ul.board_body li")
    
    if not post_items:
        raise Exception("장학 공지 게시물 리스트를 찾을 수 없습니다. CSS Selector를 확인해주세요.")

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

        # 2. 날짜 추출
        # (주의: 실제 홈페이지 소스코드에서 날짜가 들어있는 태그의 클래스명을 확인해야 합니다. 보통 span.date 사용)
        date_tag = item.select_one("span.date") 
        
        post_date = "1900-01-01" # 기본값
        
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            try:
                # '2023.10.25' -> '2023-10-25' 변환
                post_date = date_text.replace(".", "-")
            except:
                pass
        
        posts.append({
            "title": title,
            "link": link,
            "date": post_date
        })

    # 3. 날짜(date)를 기준으로 내림차순(최신순) 정렬
    if not posts:
        raise Exception("유효한 장학 공지 게시물을 찾지 못했습니다.")

    posts.sort(key=lambda x: x["date"], reverse=True)

    # 가장 최신 글 선택
    latest_post = posts[0]
    
    return latest_post["title"], latest_post["link"]

def send_to_discord(title, link):
    """
    디스코드 웹훅으로 새로운 장학 공지사항 알림을 보냅니다.
    """
    WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
    
    if not WEBHOOK_URL:
        print("🔔 알림: DISCORD_WEBHOOK 환경 변수가 설정되지 않아 메시지를 보내지 않습니다.")
        return
        
    data = {
        # 3. 메시지 내용을 장학 공지에 맞게 유지
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
        # 날짜순 정렬 로직 적용
        latest_title, latest_link = fetch_latest_notice_by_date()
        
        print("✅ 장학 공지 크롤링 성공 (날짜 정렬 적용)!")
        print(f"   - 감지된 최신 제목: {latest_title}")
        print(f"   - 이전에 보낸 제목: {last_title if last_title else '없음'}")

        if latest_title != last_title:
            print("🚀 새로운 장학 공지를 발견했습니다! 알림을 보냅니다.")
            send_to_discord(latest_title, latest_link)
            
            with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                f.write(latest_title)
        else:
            print("✅ 새로운 장학 공지가 없습니다.")
            # 파일이 없으면 생성해두기
            if not os.path.exists(LAST_NOTICE_FILE):
                 with open(LAST_NOTICE_FILE, "w", encoding="utf-8") as f:
                    f.write(latest_title)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
