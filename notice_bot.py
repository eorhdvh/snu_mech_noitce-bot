import requests
from bs4 import BeautifulSoup
import os
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
URL = "https://me.snu.ac.kr/%ea%b3%b5%ed%86%b5-%ea%b3%b5%ec%a7%80%ec%82%ac%ed%95%ad/"

def fetch_notices():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, verify=False)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # 게시글 제목과 링크 추출 (사이트 구조에 맞춰 수정 필요)
    notices = []
    for a in soup.select("td.title a"):  # 실제 사이트 HTML 구조 확인 필요
        title = a.get_text(strip=True)
        link = a["href"]
        if not link.startswith("http"):
            link = "https://me.snu.ac.kr" + link
        notices.append(f"{title}\n{link}")
    return notices[:5]  # 최신 5개만

def send_to_discord(messages):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        return
    content = "\n\n".join(messages)
    payload = {"content": content}
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    res.raise_for_status()
    print("디스코드로 공지사항 전송 완료")

if __name__ == "__main__":
    notices = fetch_notices()
    if notices:
        send_to_discord(notices)
    else:
        print("공지사항을 가져오지 못했습니다.")
