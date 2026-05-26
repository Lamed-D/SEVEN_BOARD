import sqlite3
import os

DATABASE_FILE = 'seven_board.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # 컬렉션을 dict처럼 다룰 수 있게 설정
    conn.execute("PRAGMA foreign_keys = ON") # 외래키 제약조건 활성화
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 사용자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        position TEXT NOT NULL,
        avatar_url TEXT,
        status TEXT DEFAULT 'Online',
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    
    # 2. 채팅방 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_rooms (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        is_group_chat INTEGER DEFAULT 0 NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    
    # 3. 채팅방 참여자 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_room_members (
        room_id TEXT,
        user_id TEXT,
        joined_at TEXT DEFAULT (datetime('now', 'localtime')),
        PRIMARY KEY (room_id, user_id),
        FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # 4. 채팅 메시지 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        room_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        message TEXT,
        file_url TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (room_id) REFERENCES chat_rooms(id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')
    
    # 5. 게시판 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        author_id TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        views INTEGER DEFAULT 0 NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')
    
    # 6. 댓글 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        author_id TEXT NOT NULL,
        content TEXT NOT NULL,
        parent_id TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
    )
    ''')
    
    # 7. 식단표 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menus (
        id TEXT PRIMARY KEY,
        menu_date TEXT UNIQUE NOT NULL,
        lunch_menu TEXT NOT NULL,
        dinner_menu TEXT,
        created_by TEXT,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    # 8. 식단 평점 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_ratings (
        id TEXT PRIMARY KEY,
        menu_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
        feedback TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(menu_id, user_id),
        FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # 9. 업무용 서류 양식 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        file_url TEXT NOT NULL,
        version TEXT DEFAULT '1.0' NOT NULL,
        download_count INTEGER DEFAULT 0 NOT NULL,
        created_by TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    # 10. 사내 네트워크 IP 관리 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS network_ips (
        id TEXT PRIMARY KEY,
        ip_address TEXT UNIQUE NOT NULL,
        mac_address TEXT,
        assigned_user_id TEXT,
        device_type TEXT NOT NULL,
        memo TEXT,
        is_active INTEGER DEFAULT 1 NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')
    
    # --- 시드(Seed) 데이터 주입 ---
    # 1. 가짜 사용자 계정 추가 (비밀번호: '1234' 단순 텍스트로 저장)
    users = [
        ('EMP001', 'minseo@seven.com', '1234', '봉민서', '기획본부', '팀장', '/static/uploads/profiles/minseo.png', 'Online', 1),
        ('EMP002', 'eunchan@seven.com', '1234', '박은찬', '개발1팀', '연구원', '/static/uploads/profiles/eunchan.png', 'Online', 0),
        ('EMP003', 'jungwoo@seven.com', '1234', '박정우', '개발2팀', '연구원', '/static/uploads/profiles/jungwoo.png', 'Away', 0),
        ('EMP004', 'geonchang@seven.com', '1234', '송건창', '홍보디자인팀', '대리', '/static/uploads/profiles/geonchang.png', 'Offline', 0)
    ]
    for u in users:
        cursor.execute('''
        INSERT OR IGNORE INTO users (id, email, password, name, department, position, avatar_url, status, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', u)
        
    # 2. 기본 채팅방 개설 및 멤버 연결
    rooms = [
        ('ROOM001', '럭키세븐 전체 소통방', 1),
        ('ROOM002', '개발 및 코딩 협업방', 1)
    ]
    for r in rooms:
        cursor.execute('INSERT OR IGNORE INTO chat_rooms (id, name, is_group_chat) VALUES (?, ?, ?)', r)
        
    # 모든 사원을 기본 채팅방 2개에 모두 가입시킴
    for r_id in ['ROOM001', 'ROOM002']:
        for u_id in ['EMP001', 'EMP002', 'EMP003', 'EMP004']:
            cursor.execute('INSERT OR IGNORE INTO chat_room_members (room_id, user_id) VALUES (?, ?)', (r_id, u_id))
            
    # 기본 채팅 메시지 등록
    messages = [
        ('MSG001', 'ROOM001', 'EMP001', '여러분 반갑습니다! 럭키세븐의 SEVEN_BOARD 메신저가 활성화되었습니다. 😊', None, '2026-05-26 12:00:00'),
        ('MSG002', 'ROOM001', 'EMP002', '우와, 실시간 숏 폴링으로 작동해서 아주 빠르고 안정적이네요! 🚀', None, '2026-05-26 12:01:00'),
        ('MSG003', 'ROOM001', 'EMP003', '반갑습니다! 코딩 담당 박정우입니다. 열심히 만들어봅시다.', None, '2026-05-26 12:02:00'),
        ('MSG004', 'ROOM001', 'EMP004', '디자인 및 PPT 담당 송건창입니다. 화면 구성이 깔끔해서 마음에 드네요!', None, '2026-05-26 12:03:00')
    ]
    for msg in messages:
        cursor.execute('''
        INSERT OR IGNORE INTO chat_messages (id, room_id, sender_id, message, file_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', msg)

    # 3. 기본 게시글 및 댓글 시드 데이터
    posts = [
        ('POST001', 'EMP001', 'Notice', '[필독] SEVEN_BOARD 통합 시스템 런칭 및 사용 가이드', 
         '임직원 여러분 반갑습니다. 7팀 럭키세븐에서 개발한 사내 포털 **SEVEN_BOARD**가 정식 런칭되었습니다!\n\n본 시스템은 사내 메신저, 자유/공지 게시판, 매일 업데이트되는 식단표 평점 관리, 행정 서류 양식 관리 및 IP 할당 검색 조회를 하나로 합친 올인원 업무 포털입니다.\n\n각 탭별 기능을 자유롭게 테스트하시고 피드백을 남겨주세요!', 12),
        ('POST002', 'EMP002', 'Free', 'SQLite와 Flask 조합이 생각보다 엄청 견고하네요.', 
         '이번 사내 시스템 설계 시 Next.js + PostgreSQL 대신 Flask + SQLite 조합을 썼는데 로컬에서 구동 속도도 압도적이고 파일 하나로 관리가 끝나서 Vibe Coding하기 최고인 것 같습니다. 💻\n\n다들 어떻게 생각하시나요?', 28)
    ]
    for p in posts:
        cursor.execute('''
        INSERT OR IGNORE INTO posts (id, author_id, category, title, content, views)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', p)
        
    comments = [
        ('COM001', 'POST001', 'EMP002', '런칭을 진심으로 축하드립니다! UI가 너무 깔끔해요.', None),
        ('COM002', 'POST002', 'EMP003', '맞아요! 복잡한 설정 없이 바로 파일 하나로 실행되니 너무 간편하네요.', None),
        ('COM003', 'POST002', 'EMP004', '여기에 Tailwind CDN까지 끼얹으니까 디자인 속도도 미쳤습니다. 강추!', 'COM002')
    ]
    for c in comments:
        cursor.execute('''
        INSERT OR IGNORE INTO comments (id, post_id, author_id, content, parent_id)
        VALUES (?, ?, ?, ?, ?)
        ''', c)

    # 4. 식단 데이터 (오늘과 이번 주 메뉴 등록)
    import datetime
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    menus = [
        ('MENU001', yesterday_str, '수제돈까스, 양배추샐러드, 스프, 배추김치', '얼큰우거지갈비탕, 계란찜, 깍두기, 요구르트', 'EMP001'),
        ('MENU002', today_str, '제육볶음, 모듬쌈, 우렁강된장, 미역국, 석박지', '닭갈비덮밥, 가쓰오장국, 무쌈, 군만두, 단무지', 'EMP001'),
        ('MENU003', tomorrow_str, '소불고기전골, 감자조림, 오이소박이, 청국장', '짜장면, 볶음밥, 짬뽕국물, 탕수육, 배추김치', 'EMP001')
    ]
    for m in menus:
        cursor.execute('''
        INSERT OR IGNORE INTO menus (id, menu_date, lunch_menu, dinner_menu, created_by)
        VALUES (?, ?, ?, ?, ?)
        ''', m)
        
    # 식단 평점 시드
    ratings = [
        ('RAT001', 'MENU002', 'EMP002', 5, '제육볶음 고기가 두툼하고 쌈채소가 너무 싱싱해서 정말 맛있었습니다! 👍'),
        ('RAT002', 'MENU002', 'EMP003', 4, '우렁강된장이 밥도둑이네요. 든든하게 먹었습니다.')
    ]
    for r in ratings:
        cursor.execute('''
        INSERT OR IGNORE INTO menu_ratings (id, menu_id, user_id, rating, feedback)
        VALUES (?, ?, ?, ?, ?)
        ''', r)

    # 5. 서류 양식 데이터
    docs = [
        ('DOC001', '연차/휴가 신청서 양식', '연차, 반차, 경조사 휴가 신청용 표준 서식 서류입니다.', 'HR', '/static/uploads/docs/연차휴가신청서_v1.0.docx', '1.0', 14, 'EMP001'),
        ('DOC002', '업무 기안서 서식', '부서별 품의, 결재, 예산 집행 기획 시 사용하는 표준 양식입니다.', 'Finance', '/static/uploads/docs/업무기안서_v1.1.xlsx', '1.1', 8, 'EMP001'),
        ('DOC003', '지출결의서 서식', '법인카드 사용 내역 및 영수증 증빙 청구용 지출 서류입니다.', 'Finance', '/static/uploads/docs/지출결의서_v1.0.xlsx', '1.0', 25, 'EMP001')
    ]
    for d in docs:
        cursor.execute('''
        INSERT OR IGNORE INTO documents (id, title, description, category, file_url, version, download_count, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', d)

    # 6. 네트워크 IP 데이터
    ips = [
        ('IP001', '192.168.10.11', 'AA:BB:CC:DD:EE:01', 'EMP001', 'Laptop', '봉민서 팀장 업무용 맥북', 1),
        ('IP002', '192.168.10.12', 'AA:BB:CC:DD:EE:02', 'EMP002', 'Desktop', '박은찬 개발용 메인 PC', 1),
        ('IP003', '192.168.10.13', 'AA:BB:CC:DD:EE:03', 'EMP003', 'Desktop', '박정우 코딩 테스트 PC', 1),
        ('IP004', '192.168.10.50', 'AA:BB:CC:DD:EE:99', None, 'Test Phone', '서버 테스트용 공용 단말기', 1)
    ]
    for ip in ips:
        cursor.execute('''
        INSERT OR IGNORE INTO network_ips (id, ip_address, mac_address, assigned_user_id, device_type, memo, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ip)
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # 로컬에서 단독 실행 시 테스트
    init_db()
    print("Database successfully initialized!")
