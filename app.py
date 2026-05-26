import os
import uuid
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'luckyseven_secret_key_for_vibe_coding'

# 업로드 관련 폴더 정의 및 자동 생성
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB 파일 업로드 허용

# 필수 폴더들 사전에 자동 생성
REQUIRED_FOLDERS = [
    UPLOAD_FOLDER,
    os.path.join(UPLOAD_FOLDER, 'profiles'),
    os.path.join(UPLOAD_FOLDER, 'docs'),
    os.path.join(UPLOAD_FOLDER, 'chats'),
    os.path.join(UPLOAD_FOLDER, 'posts')
]
for folder in REQUIRED_FOLDERS:
    os.makedirs(folder, exist_ok=True)

# 데이터베이스 초기화 및 가짜 파일 시드 생성
init_db()

# 로컬 서류 양식 샘플 파일들 자동 생성 (없을 경우 텍스트 파일로 더미 생성)
dummy_docs = {
    '연차휴가신청서_v1.0.docx': '연차휴가신청서 표준 양식 문서입니다.',
    '업무기안서_v1.1.xlsx': '업무기안서 스프레드시트 템플릿입니다.',
    '지출결의서_v1.0.xlsx': '지출결의서 영수증 증빙용 표준 양식입니다.'
}
doc_dir = os.path.join(UPLOAD_FOLDER, 'docs')
for name, content in dummy_docs.items():
    path = os.path.join(doc_dir, name)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

# 로그인 데코레이터
def login_required(f):
    import functools
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 모든 요청 전에 사용자 컨텍스트 로딩
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        conn = get_db_connection()
        g.user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

# ----------------- 1. 인증 라우트 (Auth) -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_input')  # 사번 또는 이메일
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE (id = ? OR email = ?) AND password = ?',
            (login_input, login_input, password)
        ).fetchone()
        conn.close()
        
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            
            # 접속 시 상태를 Online으로 변경
            conn = get_db_connection()
            conn.execute("UPDATE users SET status = 'Online' WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
        else:
            error = '사번/이메일 또는 비밀번호가 올바르지 않습니다.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        # 로그아웃 시 상태를 Offline으로 변경
        conn = get_db_connection()
        conn.execute("UPDATE users SET status = 'Offline' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
    session.clear()
    return redirect(url_for('login'))


# ----------------- 2. 메인 대시보드 (Dashboard) -----------------

@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # 📢 최근 공지사항 3개 조회
    notices = conn.execute('''
        SELECT p.*, u.name as author_name, u.avatar_url as author_avatar
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.category = 'Notice'
        ORDER BY p.created_at DESC LIMIT 3
    ''').fetchall()
    
    # 🍱 오늘의 식단
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    today_menu = conn.execute('SELECT * FROM menus WHERE menu_date = ?', (today_str,)).fetchone()
    
    menu_rating_avg = 0
    if today_menu:
        avg_row = conn.execute('SELECT AVG(rating) as avg_r FROM menu_ratings WHERE menu_id = ?', (today_menu['id'],)).fetchone()
        if avg_row['avg_r']:
            menu_rating_avg = round(avg_row['avg_r'], 1)
            
    # 🌐 내 네트워크 IP 조회
    user_id = session['user_id']
    my_ip = conn.execute('SELECT * FROM network_ips WHERE assigned_user_id = ?', (user_id,)).fetchone()
    
    # 💬 읽지 않은 대화 요약 (마지막 3개 메시지)
    recent_messages = conn.execute('''
        SELECT cm.*, cr.name as room_name, u.name as sender_name
        FROM chat_messages cm
        JOIN chat_rooms cr ON cm.room_id = cr.id
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.sender_id != ?
        ORDER BY cm.created_at DESC LIMIT 3
    ''', (user_id,)).fetchall()
    
    # ⭐ 자주 쓰는 업무 서류 양식
    fav_docs = conn.execute('SELECT * FROM documents ORDER BY download_count DESC LIMIT 3').fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html',
        notices=notices,
        today_menu=today_menu,
        menu_rating_avg=menu_rating_avg,
        my_ip=my_ip,
        recent_messages=recent_messages,
        fav_docs=fav_docs,
        today_str=today_str
    )


# ----------------- 3. 사내 메신저 (Internal Messenger) -----------------

@app.route('/chat')
@login_required
def chat():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # 내가 가입되어 있는 채팅방 리스트 조회
    rooms = conn.execute('''
        SELECT cr.*, 
          (SELECT message FROM chat_messages WHERE room_id = cr.id ORDER BY created_at DESC LIMIT 1) as last_msg,
          (SELECT created_at FROM chat_messages WHERE room_id = cr.id ORDER BY created_at DESC LIMIT 1) as last_msg_time
        FROM chat_rooms cr
        JOIN chat_room_members crm ON cr.id = crm.room_id
        WHERE crm.user_id = ?
        ORDER BY last_msg_time DESC
    ''', (user_id,)).fetchall()
    
    # 사내 모든 사원 리스트 조회 (1:1 대화방 개설 목록용)
    all_users = conn.execute('SELECT * FROM users WHERE id != ?', (user_id,)).fetchall()
    
    # 선택된 채팅방 정보
    active_room_id = request.args.get('room_id')
    active_room = None
    messages = []
    room_members = []
    
    if active_room_id:
        active_room = conn.execute('SELECT * FROM chat_rooms WHERE id = ?', (active_room_id,)).fetchone()
        if active_room:
            # 채팅 메시지 내역 로딩
            messages = conn.execute('''
                SELECT cm.*, u.name as sender_name, u.avatar_url as sender_avatar, u.department as sender_dept
                FROM chat_messages cm
                JOIN users u ON cm.sender_id = u.id
                WHERE cm.room_id = ?
                ORDER BY cm.created_at ASC
            ''', (active_room_id,)).fetchall()
            
            # 방 멤버들 로딩
            room_members = conn.execute('''
                SELECT u.* FROM users u
                JOIN chat_room_members crm ON u.id = crm.user_id
                WHERE crm.room_id = ?
            ''', (active_room_id,)).fetchall()
            
    conn.close()
    
    return render_template(
        'chat.html',
        rooms=rooms,
        all_users=all_users,
        active_room=active_room,
        messages=messages,
        room_members=room_members
    )

# [API] 1:1 또는 그룹 채팅방 생성
@app.route('/api/chat/room/create', methods=['POST'])
@login_required
def api_create_room():
    room_name = request.form.get('room_name')
    target_user_ids = request.form.getlist('user_ids') # 여러 명 체크 가능
    
    if not room_name or not target_user_ids:
        return jsonify({'error': '필수 값이 누락되었습니다.'}), 400
        
    conn = get_db_connection()
    new_room_id = f"ROOM_{uuid.uuid4().hex[:8]}"
    is_group = 1 if len(target_user_ids) > 1 else 0
    
    # 방 생성
    conn.execute('INSERT INTO chat_rooms (id, name, is_group_chat) VALUES (?, ?, ?)', (new_room_id, room_name, is_group))
    
    # 방 멤버 추가 (나 자신 포함)
    my_id = session['user_id']
    conn.execute('INSERT INTO chat_room_members (room_id, user_id) VALUES (?, ?)', (new_room_id, my_id))
    for u_id in target_user_ids:
        conn.execute('INSERT OR IGNORE INTO chat_room_members (room_id, user_id) VALUES (?, ?)', (new_room_id, u_id))
        
    conn.commit()
    conn.close()
    
    return redirect(url_for('chat', room_id=new_room_id))

# [API] 특정 채팅방 메시지 실시간 폴링용 리스트 조회
@app.route('/api/chat/<room_id>/messages')
@login_required
def api_get_messages(room_id):
    conn = get_db_connection()
    # 최근 50개 메시지만 리로드
    messages = conn.execute('''
        SELECT cm.*, u.name as sender_name, u.avatar_url as sender_avatar, u.department as sender_dept
        FROM chat_messages cm
        JOIN users u ON cm.sender_id = u.id
        WHERE cm.room_id = ?
        ORDER BY cm.created_at ASC LIMIT 100
    ''', (room_id,)).fetchall()
    
    # 사용자들의 접속 상태도 실시간 갱신용으로 함께 수집
    members_status = conn.execute('''
        SELECT u.id, u.name, u.status 
        FROM users u
        JOIN chat_room_members crm ON u.id = crm.user_id
        WHERE crm.room_id = ?
    ''', (room_id,)).fetchall()
    
    conn.close()
    
    msg_list = []
    for m in messages:
        msg_list.append({
            'id': m['id'],
            'sender_id': m['sender_id'],
            'sender_name': m['sender_name'],
            'sender_avatar': m['sender_avatar'] if m['sender_avatar'] else '',
            'sender_dept': m['sender_dept'],
            'message': m['message'],
            'file_url': m['file_url'] if m['file_url'] else '',
            'created_at': m['created_at']
        })
        
    status_list = []
    for s in members_status:
        status_list.append({
            'id': s['id'],
            'name': s['name'],
            'status': s['status']
        })
        
    return jsonify({'messages': msg_list, 'statuses': status_list, 'my_id': session['user_id']})

# [API] 메시지 전송 및 로컬 파일 업로드
@app.route('/api/chat/<room_id>/send', methods=['POST'])
@login_required
def api_send_message(room_id):
    message = request.form.get('message', '').strip()
    file = request.files.get('file')
    
    file_url = None
    if file and file.filename != '':
        filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'chats', filename))
        file_url = f"/static/uploads/chats/{filename}"
        
    if not message and not file_url:
        return jsonify({'error': '내용 또는 파일이 비어있습니다.'}), 400
        
    conn = get_db_connection()
    msg_id = f"MSG_{uuid.uuid4().hex[:8]}"
    sender_id = session['user_id']
    
    conn.execute('''
        INSERT INTO chat_messages (id, room_id, sender_id, message, file_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (msg_id, room_id, sender_id, message, file_url))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message_id': msg_id})


# ----------------- 4. 통합 게시판 (Notice Board) -----------------

@app.route('/board')
@login_required
def board_list():
    category = request.args.get('category', 'All')
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    
    query = '''
        SELECT p.*, u.name as author_name, u.department as author_dept,
          (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        JOIN users u ON p.author_id = u.id
    '''
    params = []
    conditions = []
    
    if category != 'All':
        conditions.append('p.category = ?')
        params.append(category)
        
    if search_query:
        conditions.append('(p.title LIKE ? OR p.content LIKE ? OR u.name LIKE ?)')
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
        
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
        
    query += ' ORDER BY p.created_at DESC'
    
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('board_list.html', posts=posts, category=category, search=search_query)

@app.route('/board/<post_id>')
@login_required
def board_detail(post_id):
    conn = get_db_connection()
    
    # 조회수 증가
    conn.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
    conn.commit()
    
    # 게시글 데이터
    post = conn.execute('''
        SELECT p.*, u.name as author_name, u.department as author_dept, u.position as author_position, u.avatar_url as author_avatar
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.id = ?
    ''', (post_id,)).fetchone()
    
    if not post:
        conn.close()
        return "게시글이 존재하지 않습니다.", 404
        
    # 댓글 목록 조회 (대댓글 계층을 나누기 위해 parent_id가 없는 상위 댓글을 우선 로딩하고 파이썬 단이나 템플릿 단에서 병합)
    comments = conn.execute('''
        SELECT c.*, u.name as author_name, u.avatar_url as author_avatar, u.department as author_dept
        FROM comments c
        JOIN users u ON c.author_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()
    
    conn.close()
    
    # 댓글 트리 구조 생성
    parent_comments = [c for c in comments if c['parent_id'] is None]
    child_comments = [c for c in comments if c['parent_id'] is not None]
    
    return render_template(
        'board_detail.html',
        post=post,
        parent_comments=parent_comments,
        child_comments=child_comments
    )

@app.route('/board/write', methods=['GET', 'POST'])
@login_required
def board_write():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Free')
        
        # 권한 체크: 공지사항(Notice)은 관리자만 쓸 수 있음
        if category == 'Notice' and not g.user['is_admin']:
            return "공지사항은 관리자만 작성할 수 있습니다.", 403
            
        if not title or not content:
            return "제목과 본문을 작성해 주세요.", 400
            
        conn = get_db_connection()
        post_id = f"POST_{uuid.uuid4().hex[:8]}"
        author_id = session['user_id']
        
        conn.execute('''
            INSERT INTO posts (id, author_id, category, title, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (post_id, author_id, category, title, content))
        conn.commit()
        conn.close()
        
        return redirect(url_for('board_detail', post_id=post_id))
        
    return render_template('board_write.html')

@app.route('/board/edit/<post_id>', methods=['GET', 'POST'])
@login_required
def board_edit(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        conn.close()
        return "게시글이 존재하지 않습니다.", 404
        
    # 권한 체크: 작성자 본인 혹은 관리자만 수정 가능
    if post['author_id'] != g.user['id'] and not g.user['is_admin']:
        conn.close()
        return "수정 권한이 없습니다.", 403
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Free')
        
        if category == 'Notice' and not g.user['is_admin']:
            conn.close()
            return "공지사항 권한이 없습니다.", 403
            
        conn.execute('''
            UPDATE posts 
            SET title = ?, content = ?, category = ?, updated_at = (datetime('now', 'localtime'))
            WHERE id = ?
        ''', (title, content, category, post_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('board_detail', post_id=post_id))
        
    conn.close()
    return render_template('board_write.html', post=post)

@app.route('/board/delete/<post_id>')
@login_required
def board_delete(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        conn.close()
        return "게시글이 존재하지 않습니다.", 404
        
    if post['author_id'] != g.user['id'] and not g.user['is_admin']:
        conn.close()
        return "삭제 권한이 없습니다.", 403
        
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('board_list'))

# [API] 댓글 및 대댓글 작성
@app.route('/api/posts/<post_id>/comments', methods=['POST'])
@login_required
def api_add_comment(post_id):
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id')  # 대댓글일 경우 부모 댓글 ID
    
    if not content:
        return jsonify({'error': '댓글 내용을 입력해 주세요.'}), 400
        
    conn = get_db_connection()
    comment_id = f"COM_{uuid.uuid4().hex[:8]}"
    author_id = session['user_id']
    
    conn.execute('''
        INSERT INTO comments (id, post_id, author_id, content, parent_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (comment_id, post_id, author_id, content, parent_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('board_detail', post_id=post_id))


# ----------------- 5. 식단표 조회 (Cafeteria Menu) -----------------

@app.route('/menu')
@login_required
def menu():
    conn = get_db_connection()
    
    # 이번 주 등록된 모든 식단 긁어오기 (최신 순)
    menus = conn.execute('SELECT * FROM menus ORDER BY menu_date DESC LIMIT 5').fetchall()
    
    # 각 식단의 평균 평점 묶어서 전송
    menu_ratings_stats = {}
    for m in menus:
        stats = conn.execute('''
            SELECT AVG(rating) as avg_r, COUNT(*) as count_r 
            FROM menu_ratings WHERE menu_id = ?
        ''', (m['id'],)).fetchone()
        
        feedbacks = conn.execute('''
            SELECT mr.*, u.name as user_name 
            FROM menu_ratings mr
            JOIN users u ON mr.user_id = u.id
            WHERE mr.menu_id = ? AND mr.feedback IS NOT NULL AND mr.feedback != ''
            ORDER BY mr.created_at DESC
        ''', (m['id'],)).fetchall()
        
        menu_ratings_stats[m['id']] = {
            'avg': round(stats['avg_r'], 1) if stats['avg_r'] else 0,
            'count': stats['count_r'],
            'feedbacks': feedbacks
        }
        
    conn.close()
    
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('menu.html', menus=menus, stats=menu_ratings_stats, today_str=today_str)

# [API] 식단 별점 및 한줄평 피드백 등록
@app.route('/api/menus/<menu_id>/rate', methods=['POST'])
@login_required
def api_rate_menu(menu_id):
    rating = request.form.get('rating')
    feedback = request.form.get('feedback', '').strip()
    
    if not rating:
        return "평점이 누락되었습니다.", 400
        
    conn = get_db_connection()
    user_id = session['user_id']
    rating_id = f"RAT_{uuid.uuid4().hex[:8]}"
    
    # SQLite 특화 INSERT OR REPLACE 쿼리 활용
    conn.execute('''
        INSERT INTO menu_ratings (id, menu_id, user_id, rating, feedback)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(menu_id, user_id) DO UPDATE SET
            rating = excluded.rating,
            feedback = excluded.feedback,
            created_at = (datetime('now', 'localtime'))
    ''', (rating_id, menu_id, user_id, int(rating), feedback))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('menu'))


# ----------------- 6. 업무용 서류 양식 관리 (Document Template) -----------------

@app.route('/documents')
@login_required
def documents():
    category = request.args.get('category', 'All')
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    
    query = 'SELECT * FROM documents'
    params = []
    conditions = []
    
    if category != 'All':
        conditions.append('category = ?')
        params.append(category)
        
    if search_query:
        conditions.append('(title LIKE ? OR description LIKE ?)')
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
        
    query += ' ORDER BY created_at DESC'
    
    docs = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('documents.html', docs=docs, category=category, search=search_query)

# 서류 양식 다운로드 트래커 API (클릭 시 횟수 1 올린 뒤 파일 실 전송)
@app.route('/documents/<doc_id>/download')
@login_required
def download_document(doc_id):
    conn = get_db_connection()
    doc = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    
    if not doc:
        conn.close()
        return "문서가 존재하지 않습니다.", 404
        
    # 다운로드 수 증가
    conn.execute('UPDATE documents SET download_count = download_count + 1 WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()
    
    # 로컬 static/uploads/docs/ 폴더에서 해당 파일 다운로드 서빙
    filename = os.path.basename(doc['file_url'])
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'docs'), filename, as_attachment=True)


# ----------------- 7. 사내 네트워크 IP 조회 (Internal Network IP) -----------------

@app.route('/network')
@login_required
def network():
    conn = get_db_connection()
    
    # 전체 IP 리스트 가져오기
    ips = conn.execute('''
        SELECT n.*, u.name as user_name, u.department as user_dept, u.position as user_pos
        FROM network_ips n
        LEFT JOIN users u ON n.assigned_user_id = u.id
        ORDER BY n.ip_address ASC
    ''').fetchall()
    
    conn.close()
    
    # 접속한 임직원의 실제 IP 자동 감지 (로컬 테스트 환경 시 '127.0.0.1' 혹은 'localhost')
    client_ip = request.remote_addr
    if client_ip == '::1':
        client_ip = '127.0.0.1'
        
    return render_template('network.html', ips=ips, client_ip=client_ip)

# [API] 신규 IP 할당 신청 및 등록
@app.route('/api/network/register', methods=['POST'])
@login_required
def api_register_ip():
    ip_address = request.form.get('ip_address', '').strip()
    mac_address = request.form.get('mac_address', '').strip()
    device_type = request.form.get('device_type', 'Laptop')
    memo = request.form.get('memo', '').strip()
    
    if not ip_address:
        return "IP 주소는 필수입니다.", 400
        
    conn = get_db_connection()
    
    # 1. IP 중복 검사
    existing_ip = conn.execute('SELECT * FROM network_ips WHERE ip_address = ?', (ip_address,)).fetchone()
    if existing_ip:
        conn.close()
        # Vibe coding 경고: 중복 알림 메시지 세팅
        error_msg = f"네트워크 에러: IP {ip_address}는 이미 다른 사원 또는 장비에 등록되어 충돌 위험이 있습니다!"
        return render_template('network.html', ips=conn.execute('''
            SELECT n.*, u.name as user_name, u.department as user_dept, u.position as user_pos
            FROM network_ips n
            LEFT JOIN users u ON n.assigned_user_id = u.id
            ORDER BY n.ip_address ASC
        ''').fetchall(), client_ip=ip_address, error=error_msg)
        
    ip_id = f"IP_{uuid.uuid4().hex[:8]}"
    user_id = session['user_id']
    
    conn.execute('''
        INSERT INTO network_ips (id, ip_address, mac_address, assigned_user_id, device_type, memo, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (ip_id, ip_address, mac_address, user_id, device_type, memo))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('network'))


if __name__ == '__main__':
    # Flask 앱 5000번 포트로 백그라운드 구동 가능하도록 실행
    app.run(host='0.0.0.0', port=5000, debug=True)
