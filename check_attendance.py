import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

now = datetime.now(ZoneInfo("Asia/Seoul"))

if now.hour < 9 or now.hour >= 24:
    print("운영 시간 아님")
    exit(0)
    
USERS_JSON = os.environ["USERS_JSON"]
STATE_FILE = "attendance_state.json"

users = json.loads(USERS_JSON)


year = now.strftime("%Y")
month = now.strftime("%m")
today = now.strftime("%Y-%m-%d")

state = {
    "notified": [],
    "sessions": {}
}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

state.setdefault("notified", [])
state.setdefault("sessions", {})

notified = set(state["notified"])


def send_discord(webhook, message):
    requests.post(webhook, json={"content": message}, timeout=15)


def get_saved_session(mbr_id):
    return state["sessions"].get(str(mbr_id))


def save_session(mbr_id, jsessionid):
    state["sessions"][str(mbr_id)] = jsessionid


def fetch_attendance(jsessionid, mbr_id):
    url = (
        "https://api.usr.codyssey.kr/rest/secom/detail"
        f"?mbrId={mbr_id}&year={year}&month={month}"
    )

    return requests.get(
        url,
        headers={
            "Accept": "application/json",
            "Origin": "https://usr.codyssey.kr",
            "Referer": "https://usr.codyssey.kr/",
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": f"JSESSIONID={jsessionid}",
        },
        timeout=15,
    )


def login_and_get_session(user_id, password):
    session = requests.Session()

    res = session.post(
        "https://api.ams.codyssey.kr/authenticate",
        data={
            "userId": user_id,
            "password": password,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://ams.codyssey.kr",
            "Referer": "https://ams.codyssey.kr/",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=15,
    )

    if res.status_code != 200:
        return None

    return session.cookies.get("JSESSIONID")


def is_valid_attendance_response(res):
    if res.status_code != 200:
        return False

    content_type = res.headers.get("content-type", "")

    if "application/json" not in content_type:
        return False

    try:
        data = res.json()
    except Exception:
        return False

    return data.get("success") is True or "detail_list" in data


for user in users:
    name = user["name"]
    user_id = user["codyssey_id"]
    password = user["codyssey_password"]
    mbr_id = str(user["mbr_id"])
    webhook = user["discord_webhook"]

    jsessionid = get_saved_session(mbr_id)

    res = None

    if jsessionid:
        res = fetch_attendance(jsessionid, mbr_id)

    if not jsessionid or not is_valid_attendance_response(res):
        print(f"{name}: 세션 만료 또는 없음 → 재로그인")

        new_jsessionid = login_and_get_session(user_id, password)

        if not new_jsessionid:
            send_discord(
                webhook,
                f"⚠️ {name} 코디세이 로그인 실패\n\n아이디/비밀번호를 확인해주세요."
            )
            print(f"{name}: 로그인 실패")
            continue

        save_session(mbr_id, new_jsessionid)

        res = fetch_attendance(new_jsessionid, mbr_id)

        if not is_valid_attendance_response(res):
            send_discord(
                webhook,
                f"⚠️ {name} 출입기록 조회 실패\n\nmbrId 또는 세션 상태를 확인해주세요."
            )
            print(f"{name}: 출입기록 조회 실패")
            continue
    else:
        print(f"{name}: 저장된 세션 재사용")

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
