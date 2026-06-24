# Codyssey Attendance Discord Alert

코디세이 출입시간 현황을 주기적으로 확인하고, 새로운 입실/퇴실 기록이 생기면 Discord로 알림을 보내는 자동화 프로젝트입니다.

## 기능

* 코디세이 자동 로그인
* 출입시간 API 조회
* 입실 기록 감지
* 퇴실 기록 감지
* 이미 알림 보낸 기록 중복 방지
* Discord Webhook 알림 전송
* cron-job.org를 이용한 5분/10분 주기 실행

## 동작 구조

```text
cron-job.org
    ↓ 정해진 시간마다 GitHub Actions 실행
GitHub Actions
    ↓ Python 스크립트 실행
Codyssey 로그인
    ↓
출입시간 조회
    ↓
새로운 입실/퇴실 기록 확인
    ↓
Discord Webhook 알림
```

---

# 1. 준비물

아래 4개가 필요합니다.

```text
1. GitHub 계정
2. Discord 계정
3. Codyssey 계정
4. cron-job.org 계정
```

---

# 2. 저장소 Fork

이 저장소를 본인 GitHub 계정으로 Fork합니다.

```text
Fork 버튼 클릭
↓
Create fork
```

Fork 후 본인 저장소로 이동합니다.

예시:

```text
https://github.com/본인아이디/codyssey-attendance-discord
```

---

# 3. Discord Webhook 만들기

## 3-1. Discord 서버 또는 채널 준비

알림을 받을 Discord 서버 또는 비공개 채널을 준비합니다.

추천 채널명:

```text
#codyssey-alert
#출입알림
#입실퇴실
```

출입시간은 개인 정보이므로 공용 채널보다는 본인만 볼 수 있는 채널을 권장합니다.

## 3-2. Webhook 생성

Discord에서 알림 받을 채널의 톱니바퀴를 클릭합니다.

```text
채널 편집
↓
연동
↓
웹후크
↓
새 웹후크
```

Webhook 이름 예시:

```text
CodyBot
Codyssey Attendance Bot
```

## 3-3. Webhook URL 복사

```text
웹후크 URL 복사
```

복사한 URL은 GitHub Secret에 등록할 예정입니다.

예시 형태:

```text
https://discord.com/api/webhooks/숫자/긴문자열
```

주의:

```text
Webhook URL은 비밀번호처럼 관리해야 합니다.
노출되면 다른 사람이 해당 채널에 메시지를 보낼 수 있습니다.
```

---

# 4. Codyssey mbrId 찾기

mbrId는 코디세이 내부 회원 번호입니다.

출입시간 API를 조회할 때 필요합니다.

## mbrId 확인 방법

1. 코디세이 로그인
2. 출입시간 현황 페이지 접속
3. 개발자 도구 열기

   * Windows: `F12`
   * Mac: `Command + Option + I`
4. `Network` 탭 클릭
5. 상단 검색창에 아래 단어 입력

```text
mbrId
```

6. 검색 결과에서 `detail` 요청 클릭
7. `Request URL` 또는 `Headers`에서 `mbrId=` 뒤 숫자 확인

예시:

```text
https://api.usr.codyssey.kr/rest/secom/detail?mbrId=숫자&year=2026&month=06
```


즉 GitHub Secret에는 아래처럼 등록합니다.

```text
Name: CODYSSEY_MBR_ID
Secret: 숫자
```

---

# 5. GitHub Secrets 등록

Fork한 저장소에서 아래로 이동합니다.

```text
Settings
↓
Secrets and variables
↓
Actions
↓
New repository secret
```

아래 4개를 등록합니다.

## 5-1. CODYSSEY_USER_ID

Name:

```text
CODYSSEY_USER_ID
```

Secret:

```text
본인 코디세이 로그인 아이디
```

예시:

```text
example@naver.com
```

## 5-2. CODYSSEY_PASSWORD

Name:

```text
CODYSSEY_PASSWORD
```

Secret:

```text
본인 코디세이 비밀번호
```

## 5-3. CODYSSEY_MBR_ID

Name:

```text
CODYSSEY_MBR_ID
```

Secret:

```text
본인 mbrId
```

예시:

```text
1000285048
```

## 5-4. DISCORD_WEBHOOK

Name:

```text
DISCORD_WEBHOOK
```

Secret:

```text
Discord Webhook URL
```

예시:

```text
https://discord.com/api/webhooks/...
```

주의:

```text
Secret Name에는 공백이 들어가면 안 됩니다.
값까지 Name에 넣으면 안 됩니다.
```

잘못된 예:

```text
CODYSSEY_MBR_ID = 1000285048
```

올바른 예:

```text
Name: CODYSSEY_MBR_ID
Secret: 1000285048
```

---

# 6. GitHub Actions 권한 설정

저장소에서 아래로 이동합니다.

```text
Settings
↓
Actions
↓
General
```

아래 항목을 확인합니다.

## Actions permissions

다음 항목 선택:

```text
Allow all actions and reusable workflows
```

## Workflow permissions

다음 항목 선택:

```text
Read and write permissions
```

저장 버튼을 누릅니다.

이 설정이 필요한 이유:

```text
attendance_state.json 파일에 이미 알림 보낸 기록을 저장하기 위해 필요합니다.
```

---

# 7. 수동 실행 테스트

GitHub 저장소에서:

```text
Actions
↓
Codyssey Attendance Alert
↓
Run workflow
↓
Run workflow
```

실행 후 로그를 확인합니다.

정상 로그 예시:

```text
Run python check_attendance.py
새 알림 없음
```

또는:

```text
알림 전송 완료
```

Discord에 알림이 오면 성공입니다.

---

# 8. cron-job.org로 자동 실행 설정

GitHub Actions의 schedule은 지연될 수 있으므로, cron-job.org를 이용해 GitHub Actions를 외부에서 주기적으로 실행합니다.

## 8-1. GitHub Fine-grained Token 발급

GitHub 오른쪽 위 프로필 클릭:

```text
Settings
↓
Developer settings
↓
Personal access tokens
↓
Fine-grained tokens
↓
Generate new token
```

설정:

```text
Token name: codyssey-cron
Expiration: 90 days 또는 1 year
Repository access: Only select repositories
Repository: 본인 fork 저장소 선택
```

Permissions 설정:

```text
Actions: Read and write
Contents: Read-only
```

토큰을 생성한 후 복사합니다.

주의:

```text
토큰은 한 번만 보여줍니다.
복사하지 않고 창을 닫으면 다시 확인할 수 없습니다.
```

---

# 9. cron-job.org 설정

cron-job.org에 로그인 후 새 Cronjob을 생성합니다.

```text
CREATE CRONJOB
```

## 9-1. Common 설정

Title:

```text
Codyssey Attendance
```

URL:

```text
https://api.github.com/repos/깃허브아이디/codyssey-attendance-discord/actions/workflows/check.yml/dispatches
```

예시:

```text
https://api.github.com/repos/jinks0315/codyssey-attendance-discord/actions/workflows/check.yml/dispatches
```

Execution schedule:

```text
Every 5 minutes
```

또는:

```text
Every 10 minutes
```

추천:

```text
Every 5 minutes
```

---

## 9-2. Advanced 설정

Advanced 탭으로 이동합니다.

Request method:

```text
POST
```

Headers 추가:

```text
Authorization: Bearer 본인_GitHub_토큰
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Request body:

```json
{
  "ref": "main"
}
```

---

# 10. cron-job.org 테스트

cron-job.org에서:

```text
TEST RUN
```

을 클릭합니다.

성공하면 HTTP 상태 코드가 보통 아래처럼 나옵니다.

```text
204
```

그 다음 GitHub 저장소로 이동합니다.

```text
Actions
```

새로운 workflow run이 생기면 성공입니다.

---

# 11. cron-job.org 저장

테스트에 성공했다면:

```text
CREATE
```

버튼을 눌러 저장합니다.

이제 cron-job.org가 정해진 시간마다 GitHub Actions를 실행합니다.

---

# 12. 알림 예시

입실 알림:

```text
🟢 코디세이 입실 감지

날짜: 2026-06-24
세션: 1
입실: 10:25:53
현재 누적: 00:00:00
```

퇴실 알림:

```text
🔴 코디세이 퇴실 감지

날짜: 2026-06-24
세션: 1
퇴실: 21:58:36
세션 시간: 11:45:22
오늘 누적: 11:45:22
```

---

# 13. 중복 알림 방지

이 프로젝트는 `attendance_state.json` 파일에 이미 알림 보낸 기록을 저장합니다.

예시:

```json
{
  "notified": [
    "2026-06-24-session-1-entry-10:25:53",
    "2026-06-24-session-1-exit-21:58:36"
  ]
}
```

따라서 같은 입실/퇴실 기록은 다시 알림을 보내지 않습니다.

---

# 14. 실행 주기 추천

## 5분

```text
빠른 알림
GitHub Actions 사용량 증가
```

## 10분

```text
안정적
사용량 적음
대부분의 경우 추천
```

## 1분

```text
비추천
GitHub Actions 사용량이 많아질 수 있음
```

추천 설정:

```text
5분 또는 10분
```

---

# 15. 비용

현재 구조는 무료로 사용할 수 있습니다.

| 항목                | 비용      |
| ----------------- | ------- |
| GitHub Repository | 무료      |
| GitHub Actions    | 무료 범위 내 |
| cron-job.org      | 무료      |
| Discord Webhook   | 무료      |
| 총 비용              | 0원      |

주의:

```text
Private Repository에서 너무 자주 실행하면 GitHub Actions 무료 시간을 많이 사용할 수 있습니다.
Public Repository 사용을 권장합니다.
```

---

# 16. 보안 주의사항

아래 값은 절대 공개하지 마세요.

```text
CODYSSEY_PASSWORD
DISCORD_WEBHOOK
GitHub Personal Access Token
```

특히 GitHub 토큰이 노출되면 다른 사람이 workflow를 실행할 수 있습니다.

보안 원칙:

```text
비밀번호는 GitHub Secrets에만 저장
Webhook URL은 GitHub Secrets에만 저장
토큰은 cron-job.org Header에만 저장
코드에 직접 입력 금지
README에 직접 입력 금지
```

---

# 17. 문제 해결

## Discord 알림이 안 오는 경우

확인할 것:

```text
1. DISCORD_WEBHOOK Secret이 정확한지 확인
2. Discord Webhook이 삭제되지 않았는지 확인
3. GitHub Actions 로그 확인
4. check_attendance.py에서 "새 알림 없음"인지 확인
```

`새 알림 없음`이면 오류가 아니라 이미 알림 보낸 기록이라는 뜻입니다.

---

## GitHub Actions는 성공하는데 알림이 안 오는 경우

가능한 원인:

```text
1. 새로운 입실/퇴실 기록이 없음
2. 이미 attendance_state.json에 저장된 기록임
3. Discord Webhook URL이 잘못됨
```

---

## cron-job.org TEST RUN 후 GitHub Actions가 안 생기는 경우

확인할 것:

```text
1. URL이 정확한지 확인
2. GitHub 토큰 권한 확인
3. Authorization Header 확인
4. Request method가 POST인지 확인
5. Body에 {"ref": "main"}이 있는지 확인
```

정상 성공 코드는 보통:

```text
204
```

---

## GitHub Actions에서 로그인 실패가 뜨는 경우

확인할 것:

```text
1. CODYSSEY_USER_ID 확인
2. CODYSSEY_PASSWORD 확인
3. 코디세이 비밀번호 변경 여부 확인
4. Secret 이름에 오타가 없는지 확인
```

Secret 이름은 정확히 아래와 같아야 합니다.

```text
CODYSSEY_USER_ID
CODYSSEY_PASSWORD
CODYSSEY_MBR_ID
DISCORD_WEBHOOK
```

---

## mbrId가 틀린 경우

증상:

```text
오늘 출입 기록 없음
```

또는 기록 조회 실패.

해결:

```text
Codyssey 출입시간 현황 페이지에서 개발자 도구를 열고 Network 검색창에 mbrId를 검색한 뒤 detail 요청의 Request URL을 다시 확인합니다.
```

---

# 18. 주의사항

이 프로젝트는 본인의 코디세이 출입시간 확인을 자동화하기 위한 개인용 도구입니다.

금지:

```text
다른 사람 계정 사용
다른 사람 출입기록 조회
관리자 권한 우회
서버에 과도한 요청 전송
```

권장:

```text
본인 계정만 사용
5분 또는 10분 이상 주기로 조회
Webhook URL과 비밀번호 비공개 유지
```

---

# 19. 파일 구성

```text
.
├── .github
│   └── workflows
│       └── check.yml
├── check_attendance.py
├── requirements.txt
├── attendance_state.json
└── README.md
```

---

# 20. 전체 흐름 요약

```text
1. 저장소 Fork
2. Discord Webhook 생성
3. mbrId 확인
4. GitHub Secrets 등록
5. GitHub Actions 권한 설정
6. 수동 실행 테스트
7. GitHub Token 발급
8. cron-job.org 등록
9. TEST RUN 확인
10. CREATE 저장
11. 자동 알림 사용
```

---

# 21. License

개인 학습 및 자동화 실습 목적으로 자유롭게 사용할 수 있습니다.

단, 사용자는 본인의 계정과 본인의 출입정보에 대해서만 사용해야 합니다.
