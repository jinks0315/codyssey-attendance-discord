import os
import json
from datetime import datetime
import requests

USERS_JSON = os.environ["USERS_JSON"]
STATE_FILE = "attendance_state.json"

users = json.loads(USERS_JSON)

now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
today = now.strftime("%Y-%m-%d")

state = {"notified": []}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

notified = set(state.get("notified", []))


def send_discord(webhook, message):
    requests.post(webhook, json={"content": message}, timeout=15)


for user in users:
    name = user["name"]
    user_id = user["codyssey_id"]
    password = user["codyssey_password"]
    mbr_id = user["mbr_id"]
    webhook = user["discord_webhook"]

    session = requests.Session()

    login = session.post(
        "https://api.ams.codyssey.kr/authenticate",
        data={"userId": user_id, "password": password},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://ams.codyssey.kr",
            "Referer": "https://ams.codyssey.kr/",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=15,
    )

    if login.status_code != 200:
        send_discord(
            webhook,
            f"⚠️ {name} 코디세이 로그인 실패\n\n아이디/비밀번호를 확인해주세요.",
        )
        print(f"{name}: 로그인 실패")
        continue

    url = (
        "https://api.usr.codyssey.kr/rest/secom/detail"
        f"?mbrId={mbr_id}&year={year}&month={month}"
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
        print(f"{name}: 오늘 출입 기록 없음")
        continue

    sessions = today_data.get("sessions", [])

    if not sessions:
        print(f"{name}: 오늘 세션 없음")
        continue

    for s in sessions:
        session_no = s.get("session_no")
        entry_time = s.get("entry_time")
        exit_time = s.get("exit_time")
        duration = s.get("duration")

        entry_id = f"{mbr_id}-{today}-session-{session_no}-entry-{entry_time}"
        exit_id = f"{mbr_id}-{today}-session-{session_no}-exit-{exit_time}"

        if entry_time and entry_id not in notified:
            message = (
                f"🟢 {name} 입실 감지\n\n"
                f"날짜: {today}\n"
                f"세션: {session_no}\n"
                f"입실: {entry_time}\n"
                f"현재 누적: {today_data.get('daily_total_duration')}"
            )
            send_discord(webhook, message)
            notified.add(entry_id)
            print(f"{name}: 입실 알림 전송")

        if exit_time and exit_id not in notified:
            message = (
                f"🔴 {name} 퇴실 감지\n\n"
                f"날짜: {today}\n"
                f"세션: {session_no}\n"
                f"퇴실: {exit_time}\n"
                f"세션 시간: {duration}\n"
                f"오늘 누적: {today_data.get('daily_total_duration')}"
            )
            send_discord(webhook, message)
            notified.add(exit_id)
            print(f"{name}: 퇴실 알림 전송")

state["notified"] = sorted(notified)

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print("전체 사용자 체크 완료")
