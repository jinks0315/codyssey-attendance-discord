import os
import json
from datetime import datetime
import requests

USER_ID = os.environ["CODYSSEY_USER_ID"]
PASSWORD = os.environ["CODYSSEY_PASSWORD"]
MBR_ID = os.environ["CODYSSEY_MBR_ID"]
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

STATE_FILE = "attendance_state.json"

now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
today = now.strftime("%Y-%m-%d")

session = requests.Session()

login = session.post(
    "https://api.ams.codyssey.kr/authenticate",
    data={"userId": USER_ID, "password": PASSWORD},
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://ams.codyssey.kr",
        "Referer": "https://ams.codyssey.kr/",
        "X-Requested-With": "XMLHttpRequest",
    },
    timeout=15,
)

if login.status_code != 200:
    raise Exception(f"코디세이 로그인 실패: {login.status_code}")

url = (
    "https://api.usr.codyssey.kr/rest/secom/detail"
    f"?mbrId={MBR_ID}&year={year}&month={month}"
)

res = session.get(
    url,
    headers={
        "Accept": "application/json",
        "Origin": "https://usr.codyssey.kr",
        "Referer": "https://usr.codyssey.kr/main/access-time",
        "X-Requested-With": "XMLHttpRequest",
    },
    timeout=15,
)

data = res.json()

today_data = next(
    (item for item in data.get("detail_list", []) if item.get("date") == today),
    None,
)

if not today_data:
    print("오늘 출입 기록 없음")
    exit(0)

sessions = today_data.get("sessions", [])

if not sessions:
    print("오늘 세션 없음")
    exit(0)

last_session = sessions[-1]

current_state = {
    "date": today,
    "session_count": today_data.get("session_count"),
    "entry_time": last_session.get("entry_time"),
    "exit_time": last_session.get("exit_time"),
    "daily_total_duration": today_data.get("daily_total_duration"),
}

old_state = {}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        old_state = json.load(f)

if current_state != old_state:
    message = (
        "📌 코디세이 출입 기록 변경 감지\n\n"
        f"날짜: {current_state['date']}\n"
        f"입실: {current_state['entry_time'] or '-'}\n"
        f"퇴실: {current_state['exit_time'] or '-'}\n"
        f"세션 수: {current_state['session_count']}\n"
        f"누적 시간: {current_state['daily_total_duration']}"
    )

    requests.post(WEBHOOK, json={"content": message}, timeout=15)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_state, f, ensure_ascii=False, indent=2)

    print("알림 전송 완료")
else:
    print("변경 없음")
