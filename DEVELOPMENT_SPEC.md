# 🚀 SEVEN_BOARD 개발 명세서 (Python Flask + SQLite 기반 단순 구현)

본 문서는 **7팀 '럭키세븐'**의 통합 사내 포털 및 협업 시스템인 **SEVEN_BOARD**의 세부 기능 및 아키텍처 설계서입니다. 
인공지능(AI) 코딩 어시스턴트와의 협업(바이브 코딩, Vibe Coding)에 최적화되도록 세부 기능, 데이터베이스 스키마, API 명세, 화면 설계 및 단계별 구현 로드맵을 매우 구체적으로 정의하였습니다.

특히, Node.js나 복잡한 프론트엔드 빌드 환경 없이, 파이썬 설치만으로 즉시 구동할 수 있도록 **Flask(웹 프레임워크) + SQLite(로컬 파일 DB) + Jinja2 Templates(서버 사이드 렌더링) + Tailwind CSS CDN** 조합을 사용하여 개발 난이도를 극도로 낮춰 설계했습니다.

---

## 📌 1. 프로젝트 개요 (Overview)

### 1.1 팀 구성 및 역할
*   **팀명**: 럭키세븐 (Lucky Seven)
*   **팀장**: 봉민서 (영상 제작, 프로젝트 총괄)
*   **팀원**:
    *   **박은찬**: 코딩 (Flask / DB / Frontend 개발)
    *   **박정우**: 코딩 (Flask / DB / Frontend 개발)
    *   **송건창**: PPT 및 발표 자료 구성, 기획 보조

### 1.2 프로젝트 목표
사내 메신저, 통합 게시판, 식단표 조회, 업무용 서류 양식 관리, 사내 네트워크 IP 조회 기능을 **단일 Flask 시스템으로 통합**합니다. 
복잡한 클라우드나 빌드 설정 대신 단 하나의 파이썬 스크립트 실행과 단일 데이터베이스 파일(`seven_board.db`) 및 로컬 파일 스토리지를 사용하여 누구나 1초 만에 테스트하고 배포할 수 있는 신뢰성 높은 협업 포털을 구축합니다.

---

## 🛠️ 2. 추천 기술 스택 (Recommended Tech Stack)

파이썬 환경에서 가장 쉽고 빠르게 풀스택 웹 어플리케이션을 완성할 수 있는 초고속 Vibe Coding 스택입니다.

*   **Backend & Web Framework**: Python Flask
    *   *이유*: 파이썬 기반의 초경량 웹 프레임워크로, 가볍고 직관적이며 AI 코드 생성기가 가장 오류 없이 코드를 짜내는 도구 중 하나입니다.
*   **Frontend & Rendering**: HTML5 + Jinja2 Template (Flask 내장 템플릿 엔진)
    *   *이유*: React/Next.js처럼 복잡한 npm 패키지 설치나 빌드 과정 없이, HTML 파일 내에서 파이썬 데이터를 직접 그려줄 수 있어 초심자에게 매우 유리합니다.
*   **Styling & UI**: Tailwind CSS (CDN 연동) + FontAwesome (Icons CDN)
    *   *이유*: CSS 빌더 설치 없이 HTML `<head>`에 CDN 한 줄만 넣어주면 즉시 모던하고 세련된 UI 스타일링이 가능합니다.
*   **Database**: SQLite (Python 내장 `sqlite3` 모듈 활용)
    *   *이유*: 파이썬에 기본 내장되어 있어 추가 라이브러리 설치나 DB 계정 설정조차 불필요합니다. 파일 하나(`seven_board.db`)로 모든 데이터를 완벽하게 제어합니다.
*   **Storage (파일 저장)**: 로컬 static 폴더 스토리지 (`static/uploads/` 폴더 사용)
    *   *이유*: 업로드된 메신저 이미지나 서류 양식 파일들을 파이썬 코드로 로컬 폴더에 바로 저장하고, 웹 브라우저에서는 `/static/uploads/...` 경로로 손쉽게 호출 가능합니다.
*   **Authentication (인증)**: Flask `session` 모듈 (서명된 쿠키 기반 세션 사용)
*   **Real-time (실시간성 대체)**: Vanilla JavaScript의 `setInterval()` + `fetch()` 기반 **Short Polling**
    *   *이유*: 복잡한 웹소켓 없이, 브라우저 화면의 자바스크립트가 2초 주기로 Flask의 메시지 API를 호출(Fetch)하여 수신받은 메시지를 DOM에 업데이트해 실시간 채팅 효과를 냅니다.

---

## 📋 3. 핵심 기능별 세부 명세 (Detailed Features)

### 3.1 💬 사내 메신저 (Internal Messenger)
*   **실시간 채팅 모사 (Short Polling)**: 프론트엔드 JS에서 `setInterval`을 이용해 2초마다 해당 채팅방의 새로운 메시지를 가져오는 Flask 엔드포인트 `/api/chat/<room_id>/messages`를 자동 호출하여 갱신합니다.
*   **채팅방 생성 및 관리**:
    *   1:1 개인 채팅 및 N:N 그룹(부서별, 프로젝트별) 채팅방 개설.
    *   채팅방 이름 변경 및 참여자 초대 기능.
*   **사용자 상태 표시**: DB의 `status`를 2초마다 Polling하여 상대방 프로필 옆에 초록색(Online)/주황색(Away)/회색(Offline) 원 표시.
*   **메시지 기능**:
    *   텍스트 메시지 및 이미지/파일 전송 (Flask `werkzeug.utils.secure_filename`을 사용하여 파일 저장 후 `/static/uploads/`에 기록).
    *   메시지 안 읽은 사람 수 표시 (메시지 읽음 확인 기능).

### 3.2 📌 통합 게시판 (Notice Board)
*   **카테고리 분류**: `공지사항`(관리자만 작성 가능), `자유게시판`, `부서별 게시판`으로 구분.
*   **게시글 CRUD (생성, 조회, 수정, 삭제)**:
    *   글 작성 폼에서 여러 개의 첨부파일을 전송하면 static 폴더에 보관하고, 다운로드 링크 매핑.
    *   작성 글 수정 및 삭제 기능 (작성자 혹은 관리자만 가능하게 백엔드 검증).
*   **인터랙션 기능**:
    *   추천(좋아요) 수 토글 기능 및 상세 조회 시 조회수 1 증가.
    *   댓글 및 대댓글(답글) 작성 기능.

### 3.3 🍱 식단표 조회 (Cafeteria Menu)
*   **주간/일별 식단 표시**: Jinja2 루프를 사용하여 데이터베이스에 등록된 월~금 식사 구성을 주간 식단 카드 형태로 바인딩.
*   **오늘의 메뉴 하이라이트**: Python에서 오늘 날짜(`datetime.date.today()`)를 계산하여 일치하는 식단 정보를 대시보드 최상단 위젯으로 노출.
*   **피드백 및 평가**:
    *   별점(1~5점) 선택 및 한줄평 등록 기능.
    *   각 메뉴 평균 평점 및 후기 리스트 노출.
*   **식단 관리자 모드**: 관리자 등급 계정은 별도의 폼에서 식단을 추가/수정 가능.

### 3.4 📂 업무용 서류 양식 관리 (Document Template)
*   **양식 등록 및 다운로드**:
    *   행정 양식 파일(.docx, .xlsx, .hwp)들을 `static/templates/`에 관리하고, 임직원이 원클릭 다운로드.
*   **다운로드 수 카운터**: 다운로드 링크 클릭 시 Flask 엔드포인트 `/documents/<doc_id>/download`를 경유하게 만들어 다운로드 횟수(`download_count`)를 DB에서 1 증가시킨 후 파일을 리턴(`send_from_directory`).
*   **검색 및 즐겨찾기**: 
    *   양식 명칭 검색 및 즐겨찾기(⭐) 추가 기능.

### 3.5 🌐 사내 네트워크 IP 조회 (Internal Network IP)
*   **내 IP 자동 감지**: Flask의 `request.remote_addr`을 감지하여 사용자가 시스템에 접속하자마자 자신의 현재 네트워크 IP를 화면에 띄우고, 등록 요청을 보낼 수 있게 설계.
*   **IP 할당 전체 현황판**: 부서명, 사용자명, IP 주소, MAC 주소, 기기 구분(노트북/PC) 일람표 제공.
*   **IP 중복 감지**: 새로운 IP 등록/수정 시, SQLite DB에 이미 동일 IP가 할당되어 있는지 사전 검색하여 네트워크 충돌을 원천 차단하는 에러 메시지 반환.

---

## 🗄️ 4. 데이터베이스 설계 (SQLite Schema)

Flask 어플리케이션 실행 시 파이썬 코드로 자동 실행하여 생성할 수 있는 SQLite DDL 스키마입니다.

```sql
-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,            -- 사번 또는 사용자 고유 ID
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,         -- 비밀번호 (sha256 등으로 해싱 권장)
    name TEXT NOT NULL,
    department TEXT NOT NULL,       -- 부서 (개발, 인사, 마케팅, 기획 등)
    position TEXT NOT NULL,         -- 직급 (사원, 대리, 과장, 부장 등)
    avatar_url TEXT,                -- 프로필 이미지 경로 (/static/uploads/profiles/...)
    status TEXT DEFAULT 'Online',   -- Online, Away, Offline
    is_admin INTEGER DEFAULT 0,     -- 0: 일반 사용자, 1: 관리자
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 2. 채팅방 테이블
CREATE TABLE IF NOT EXISTS chat_rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_group_chat INTEGER DEFAULT 0 NOT NULL, -- 0: 1:1 채팅, 1: 그룹채팅
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 3. 채팅방 참여자 매핑 테이블
CREATE TABLE IF NOT EXISTS chat_room_members (
    room_id TEXT,
    user_id TEXT,
    joined_at TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. 채팅 메시지 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    message TEXT,
    file_url TEXT,                  -- static 업로드 경로
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 5. 게시판 테이블
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL,
    category TEXT NOT NULL,         -- Notice, Free, Dept_Dev 등
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    views INTEGER DEFAULT 0 NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 6. 댓글 테이블
CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,
    parent_id TEXT,                 -- 대댓글용 (대댓글이 아니라면 NULL)
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- 7. 식단표 테이블
CREATE TABLE IF NOT EXISTS menus (
    id TEXT PRIMARY KEY,
    menu_date TEXT UNIQUE NOT NULL, -- YYYY-MM-DD
    lunch_menu TEXT NOT NULL,       -- 점심 식단
    dinner_menu TEXT,               -- 저녁 식단
    created_by TEXT,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 8. 식단 평점 테이블
CREATE TABLE IF NOT EXISTS menu_ratings (
    id TEXT PRIMARY KEY,
    menu_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    feedback TEXT,                  -- 한줄평
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(menu_id, user_id),
    FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 9. 업무용 서류 양식 테이블
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,         -- HR, Finance, General 등
    file_url TEXT NOT NULL,          -- 로컬 저장 파일 경로 (/static/uploads/docs/...)
    version TEXT DEFAULT '1.0' NOT NULL,
    download_count INTEGER DEFAULT 0 NOT NULL,
    created_by TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 10. 사내 네트워크 IP 관리 테이블
CREATE TABLE IF NOT EXISTS network_ips (
    id TEXT PRIMARY KEY,
    ip_address TEXT UNIQUE NOT NULL,
    mac_address TEXT,
    assigned_user_id TEXT,
    device_type TEXT NOT NULL,       -- Laptop, Desktop 등
    memo TEXT,
    is_active INTEGER DEFAULT 1 NOT NULL, -- 0: 비활성, 1: 활성
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

---

## 🌐 5. API / Routing 설계 가이드

Flask의 Routing 시스템(`@app.route`)을 활용한 전체 백엔드 라우트 테이블입니다. HTML 페이지 렌더링과 JSON API를 모두 담당합니다.

### 5.1 웹 페이지 렌더링 라우트 (HTML Pages)
| Method | Endpoint | 설명 | 렌더링 템플릿 |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | 메인 대시보드 화면 (로그인 필요) | `templates/dashboard.html` |
| `GET` | `/login` | 로그인 화면 | `templates/login.html` |
| `GET` | `/chat` | 사내 메신저 채팅방 리스트 및 채팅창 | `templates/chat.html` |
| `GET` | `/board` | 통합 게시판 목록 (필터/검색 지원) | `templates/board_list.html` |
| `GET` | `/board/<post_id>` | 게시글 상세 페이지 및 댓글 리스트 | `templates/board_detail.html` |
| `GET` | `/board/write` | 게시글 작성/수정 양식 폼 | `templates/board_write.html` |
| `GET` | `/menu` | 주간 식단표 조회 및 별점 피드백 페이지 | `templates/menu.html` |
| `GET` | `/documents` | 서류 양식함 목록 | `templates/documents.html` |
| `GET` | `/network` | IP 할당 전체 리스트 및 신청 폼 | `templates/network.html` |

### 5.2 JSON API 라우트 (AJAX/Fetch 및 파일 전송용)
| Method | Endpoint | 설명 |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | 로그인 인증 처리 및 세션 등록 |
| `POST` | `/api/auth/logout` | 세션 클리어 및 로그아웃 처리 |
| `POST` | `/api/chat/room/create` | 채팅방 생성 및 참여자 연결 |
| `GET` | `/api/chat/<room_id>/messages` | 특정 채팅방의 메시지 최신 리스트 조회 (Short Polling API) |
| `POST` | `/api/chat/<room_id>/send` | 메시지 전송 (텍스트 및 이미지 파일 업로드 수용) |
| `POST` | `/api/posts/<post_id>/comments` | 특정 게시글에 댓글/대댓글 등록 |
| `POST` | `/api/menus/<menu_id>/rate` | 식단 한줄평 및 별점 점수 DB 입력 |
| `GET` | `/documents/<doc_id>/download` | 파일 조회수 올린 뒤 브라우저에 해당 양식 전송 |
| `POST` | `/api/network/register` | 사용자의 요청 IP 및 정보 SQLite 등록 및 중복 검증 |

---

## 🎨 6. 화면 설계 & UI/UX 가이드 (UI/UX Guide)

*   **기본 공통 템플릿 (`templates/layout.html`)**:
    *   Jinja2의 `{% block content %}`을 사용해 전체 화면에 공통 사이드바와 상단 헤더가 상시 렌더링되게 관리합니다.
    *   **Tailwind CSS (CDN)**과 **FontAwesome (아이콘 CDN)**을 포함하여 깔끔하고 모던한 다크 테마 디자인을 즉시 적용합니다.
*   **사이드바 템플릿**:
    *   좌측 사이드바에 각 페이지 이동 탭을 고정으로 두고, 하단에 로그인한 사용자 세션 정보를 바탕으로 아바타와 직급(예: **홍길동 대리**)을 노출합니다.

---

## 🗺️ 7. 바이브 코딩을 위한 단계별 구현 로드맵 (Roadmap)

Flask와 SQLite로 빠르게 개발할 수 있도록 짜인 단계별 로드맵입니다. AI 어시스턴트에게 순차적으로 질문을 주며 빌드하세요.

### Phase 1: 파이썬 프로젝트 환경 설정 ⚙️
1. 로컬 프로젝트 폴더 구조 생성:
   ```text
   SEVEN_BOARD/
   ├── app.py              # 메인 Flask 프로그램
   ├── database.py         # DB 헬퍼 함수 정의
   ├── seven_board.db      # SQLite 데이터베이스 파일 (자동 생성)
   ├── static/             # CSS, JS 및 업로드 파일
   │   ├── css/
   │   ├── js/
   │   └── uploads/        # 채팅 이미지, 첨부파일, 문서 저장용
   └── templates/          # HTML Jinja2 파일들
       ├── layout.html     # 기본 뼈대
       └── dashboard.html  # 대시보드 화면
   ```
2. 가상 환경 구축 및 필수 패키지 설치:
   *   `pip install Flask`
3. **`database.py` 작성**: Flask가 실행될 때 SQLite에 자동으로 접속하고 위의 **4장의 DDL 쿼리**가 미실행 상태라면 실행하여 테이블을 구성하고 가짜 유저(Seed 데이터) 3명(박은찬, 박정우, 봉민서)을 넣어두는 초기화 코드 작성.

### Phase 2: 기본 페이지 레이아웃 및 세션 로그인 구현 🔐
1. `templates/layout.html`에 Tailwind CDN을 장착하고 사이드바 디자인 완성.
2. `flask.session`을 이용하여 로그인된 사용자만 대시보드 및 각 탭에 접근할 수 있게 데코레이터(`@login_required`) 구현.
3. `/login` 페이지 디자인 및 로그인 인증 로직 구성.

### Phase 3: 개별 기능 순차적 Vibe Coding 🚀
1.  **통합 게시판 (Jinja2 + SQLite)**:
    *   게시글 리스트 뷰 및 게시글 상세 읽기 `/board/<post_id>` 페이지 렌더링 구현.
    *   첨부파일을 `static/uploads/` 폴더에 업로드하는 기능 연동.
2.  **사내 메신저 (Short Polling)**:
    *   `/chat` 페이지 렌더링.
    *   자바스크립트의 `setInterval(fetchMessages, 2000)` 코드를 작성하여 2초마다 Flask API에서 신규 대화 데이터를 JSON으로 받아와 채팅창 DOM에 붙여넣어 주는 스크립트 작성.
3.  **식단표 및 별점 기능**:
    *   식단 목록을 가져와 테이블/카드 뷰로 보여주는 `/menu` 라우트 구축.
    *   별점 클릭 시 AJAX(Fetch) 요청을 보내 데이터베이스 `menu_ratings`에 반영하고, 화면 리로드 없이 실시간으로 평균 평점 UI 갱신.
4.  **서류 양식함**:
    *   `static/uploads/docs/` 폴더를 만들고 임시 서류 샘플 파일 배치.
    *   파일 다운로드 시 SQLite의 `download_count` 값을 올리는 백엔드 API 구현.
5.  **사내 IP 조회**:
    *   `request.remote_addr`을 화면에 기본 노출하고 기기 타입을 선택해 SQLite에 IP를 신규 등록하는 기능 구현. 중복 발생 시 Alert 메시지 띄우기.

### Phase 4: 최종 테스트 및 통합 🎨✨
1. 브라우저 멀티 윈도우를 열어 메신저 간 실시간(Short Polling) 통신과 IP 감지가 작동하는지 점검.
2. `python app.py`로 구동 상태를 시연하고 PPT 및 영상 제작에 적합하도록 테마 컬러를 7팀의 '럭키세븐' 브랜드 컬러(예: Green, Emerald 계열)로 디테일 조정.

---
*파이썬 라이브러리 목록(`requirements.txt`) 및 SQLite 로컬 파일(`seven_board.db`)은 `.gitignore`에 추가하는 것을 권장합니다.*
