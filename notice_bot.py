import os
import requests
from bs4 import BeautifulSoup

URL = "https://me.snu.ac.kr/%ea%b3%b5%ed%86%b5-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"
# ... (이하 코드 동일) ...

def fetch_latest_notice():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
    res = requests.get(URL, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # ❗ [핵심] 더 짧고 안정적인 선택자로 변경
    # 'board_body' 클래스를 가진 ul 안의 첫 번째 li 항목(게시글) 안에 있는 링크(a)를 선택
    first_post_link = soup.select_one("ul.board_body li:nth-child(1) a")
    
    if not first_post_link:
        raise Exception("최신 공지사항 항목을 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")

    # 링크 안의 텍스트가 여러 div로 나뉘어 있을 수 있으므로 .get_text() 사용
    title = first_post_link.get_text(strip=True)
    link = first_post_link.get("href")
    
    if link and link.startswith("/"):
        link = "https://me.snu.ac.kr" + link
        
    return title, link

# ... (이하 코드 동일) ...

if __name__ == "__main__":
    try:
        latest_title, latest_link = fetch_latest_notice()
        print("✅ 크롤링 성공!")
        print(f"   - 제목: {latest_title}")
        print(f"   - 링크: {latest_link}")
        send_to_discord(latest_title, latest_link) # 필요 시 주석 해제
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
