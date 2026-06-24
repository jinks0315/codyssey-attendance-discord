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

state = {
    "notified": []
}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

notified = set(state.get("notified", []))

new_notifications = []

for s in sessions:
    session_no = s.get("session_no")
    entry_time = s.get("entry_time")
    exit_time = s.get("exit_time")
    duration = s.get("duration")

    entry_id = f"{today}-session-{session_no}-entry-{entry_time}"
    exit_id = f"{today}-session-{session_no}-exit-{exit_time}"

    if entry_time and entry_id not in notified:
        new_notifications.append({
            "id": entry_id,
            "message": (
                "🟢 코디세이 입실 감지\n\n"
                f"날짜: {today}\n"
                f"세션: {session_no}\n"
                f"입실: {entry_time}\n"
                f"현재 누적: {today_data.get('daily_total_duration')}"
            )
        })

    if exit_time and exit_id not in notified:
        new_notifications.append({
            "id": exit_id,
            "message": (
                "🔴 코디세이 퇴실 감지\n\n"
                f"날짜: {today}\n"
                f"세션: {session_no}\n"
                f"퇴실: {exit_time}\n"
                f"세션 시간: {duration}\n"
                f"오늘 누적: {today_data.get('daily_total_duration')}"
            )
        })

for item in new_notifications:
    requests.post(WEBHOOK, json={"content": item["message"]}, timeout=15)
    notified.add(item["id"])
    print(f"알림 전송: {item['id']}")

state["notified"] = sorted(notified)

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

if not new_notifications:
    print("새 알림 없음")
