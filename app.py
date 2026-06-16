 # this is the backend

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATABASE'] = 'app.db'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                tag TEXT UNIQUE NOT NULL,
                pfp_url TEXT NOT NULL,
                dark_mode INTEGER NOT NULL DEFAULT 0
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                due TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            '''
        )


@app.before_request
def setup_database():
    init_db()


def get_user_by_id(user_id):
    if not user_id:
        return None
    row = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_username_tag(username, tag):
    row = get_db().execute(
        'SELECT * FROM users WHERE username = ? AND tag = ?', (username, tag)
    ).fetchone()
    return dict(row) if row else None


def create_user(username):
    conn = get_db()
    try:
        cursor = conn.execute(
            'INSERT INTO users (username, pfp_url, dark_mode, tag) VALUES (?, ?, 0, ?)',
            (username, 'profile_photo.png', '0000')
        )
        user_id = cursor.lastrowid
        tag = str(user_id).zfill(4)
        conn.execute('UPDATE users SET tag = ? WHERE id = ?', (tag, user_id))
        conn.commit()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None


def get_current_user():
    return get_user_by_id(session.get('user_id'))


def get_assignments_for_user(user_id):
    rows = get_db().execute(
        'SELECT * FROM assignments WHERE user_id = ? ORDER BY due', (user_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def get_assignment_for_user(assignment_id, user_id):
    row = get_db().execute(
        'SELECT * FROM assignments WHERE id = ? AND user_id = ?',
        (assignment_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def count_assignments(user_id):
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM assignments WHERE user_id = ?', (user_id,)).fetchone()[0]
    completed = db.execute(
        'SELECT COUNT(*) FROM assignments WHERE user_id = ? AND completed = 1', (user_id,)
    ).fetchone()[0]
    return total, completed


def get_leaderboard():
    rows = get_db().execute(
        '''
        SELECT
            u.username,
            COUNT(a.id) AS total_assignments,
            SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) AS completed_assignments
        FROM users u
        LEFT JOIN assignments a ON a.user_id = u.id
        GROUP BY u.id
        ORDER BY
            CASE WHEN COUNT(a.id) = 0 THEN 0 ELSE SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(a.id) END DESC,
            completed_assignments DESC,
            u.username ASC
        '''
    ).fetchall()

    leaderboard = []
    for row in rows:
        total_assignments = row['total_assignments']
        completed_assignments = row['completed_assignments'] or 0
        completion_rate = int((completed_assignments * 100) / total_assignments) if total_assignments else 0
        leaderboard.append({
            'username': row['username'],
            'total_assignments': total_assignments,
            'completion_rate': completion_rate,
        })
    return leaderboard


@app.route('/')
def home():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    assignments = get_assignments_for_user(user['id'])
    return render_template('index.html', user=user, assignments=assignments)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            return render_template('register.html', error='Please enter a username.')

        user = create_user(username)
        if not user:
            return render_template('register.html', error='That username is already in use.')

        session['user_id'] = user['id']
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        tag = request.form.get('tag', '').strip()

        user = get_user_by_username_tag(username, tag)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('home'))

        return render_template('login.html', error='Login failed. Check your username and tag.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != user['username']:
            try:
                db = get_db()
                db.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user['id']))
                db.commit()
                user = get_user_by_id(user['id'])
            except sqlite3.IntegrityError:
                return render_template('profile.html', user=user, error='Username already taken!')

        if 'pfp_file' in request.files:
            file = request.files['pfp_file']
            if file.filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                db = get_db()
                db.execute(
                    'UPDATE users SET pfp_url = ? WHERE id = ?',
                    (f'uploads/{file.filename}', user['id'])
                )
                db.commit()
                user = get_user_by_id(user['id'])

        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        dark_mode = 1 if request.form.get('dark_mode') == 'on' else 0
        db = get_db()
        db.execute('UPDATE users SET dark_mode = ? WHERE id = ?', (dark_mode, user['id']))
        db.commit()
        user = get_user_by_id(user['id'])

    return render_template('settings.html', user=user)


@app.route('/stats')
def stats():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    total, completed = count_assignments(user['id'])
    pending = total - completed
    percent = int((completed / total) * 100) if total else 0
    leaderboard = get_leaderboard()

    return render_template(
        'stats.html',
        user=user,
        total=total,
        completed=completed,
        pending=pending,
        percent=percent,
        leaderboard=leaderboard,
    )

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=user)

@app.route('/clock')
def clock():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    return render_template('clock.html', user=user)

@app.route('/add', methods=['POST'])
def add_assignment():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    task = request.form.get('task', '').strip()
    due = request.form.get('due', '').strip()
    difficulty = request.form.get('difficulty', 'Easy').strip()

    if task and due:
        db = get_db()
        db.execute(
            'INSERT INTO assignments (user_id, task, due, difficulty) VALUES (?, ?, ?, ?)',
            (user['id'], task, due, difficulty),
        )
        db.commit()

    return redirect(url_for('home'))


@app.route('/complete_assignment/<int:assignment_id>', methods=['POST'])
def complete_assignment(assignment_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    assignment = get_assignment_for_user(assignment_id, user['id'])
    if assignment:
        db = get_db()
        db.execute(
            'UPDATE assignments SET completed = 1 WHERE id = ? AND user_id = ?',
            (assignment_id, user['id']),
        )
        db.commit()

    return redirect(url_for('home'))


@app.route('/edit_assignment/<int:assignment_id>', methods=['POST'])
def edit_assignment(assignment_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    due = request.form.get('due', '').strip()
    assignment = get_assignment_for_user(assignment_id, user['id'])
    if assignment and due:
        db = get_db()
        db.execute(
            'UPDATE assignments SET due = ? WHERE id = ? AND user_id = ?',
            (due, assignment_id, user['id']),
        )
        db.commit()

    return redirect(url_for('home'))


@app.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    assignment = get_assignment_for_user(assignment_id, user['id'])
    if assignment:
        db = get_db()
        db.execute('DELETE FROM assignments WHERE id = ? AND user_id = ?', (assignment_id, user['id']))
        db.commit()

    return redirect(url_for('home'))


@app.route('/delete_account')
def delete_account():
    user = get_current_user()
    if user:
        db = get_db()
        db.execute('DELETE FROM assignments WHERE user_id = ?', (user['id'],))
        db.execute('DELETE FROM users WHERE id = ?', (user['id'],))
        db.commit()
        session.pop('user_id', None)
    return redirect(url_for('register'))


if __name__ == '__main__':
    app.run(debug=True)