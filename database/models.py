import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'app_data.db')
SQL_PATH = os.path.join(BASE_DIR, 'database.sql')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_has_column(connection, table_name, column_name):
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def init_db():
    if not os.path.exists(DB_PATH):
        connection = get_connection()
        with open(SQL_PATH, 'r', encoding='utf-8') as sql_file:
            connection.executescript(sql_file.read())
        connection.commit()
        connection.close()
        return

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone() is None:
        with open(SQL_PATH, 'r', encoding='utf-8') as sql_file:
            connection.executescript(sql_file.read())
        connection.commit()
    else:
        if not table_has_column(connection, 'users', 'email'):
            connection.execute('ALTER TABLE users ADD COLUMN email TEXT')
        if not table_has_column(connection, 'users', 'department'):
            connection.execute('ALTER TABLE users ADD COLUMN department TEXT')
        connection.commit()
    connection.close()


def query_db(query, args=(), one=False):
    conn = get_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def get_user(username, password):
    return query_db(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        (username, password), one=True
    )


def get_user_by_id(user_id):
    return query_db('SELECT * FROM users WHERE id = ?', (user_id,), one=True)


def get_user_by_username(username):
    return query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)


def create_user(fullname, username, password, role='employee', email=None, department=None):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO users (fullname, username, password, role, email, department) VALUES (?, ?, ?, ?, ?, ?)',
        (fullname, username, password, role, email, department)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def create_ticket(title, category, priority, severity, description, employee_id):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tickets (title, category, priority, severity, description, employee_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (title, category, priority, severity, description, employee_id, timestamp, timestamp)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_activity(ticket_id, employee_id, 'Ticket created by employee')
    return ticket_id


def fetch_tickets_for_employee(employee_id, filters=None):
    filters = filters or {}
    query = 'SELECT * FROM tickets WHERE employee_id = ?'
    params = [employee_id]

    if filters.get('category'):
        query += ' AND category = ?'
        params.append(filters['category'])
    if filters.get('status'):
        query += ' AND status = ?'
        params.append(filters['status'])
    if filters.get('priority'):
        query += ' AND priority = ?'
        params.append(filters['priority'])
    if filters.get('severity'):
        query += ' AND severity = ?'
        params.append(filters['severity'])
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        query += ' AND (title LIKE ? OR description LIKE ? OR category LIKE ? OR priority LIKE ? OR status LIKE ?)'
        params.extend([search_term] * 5)

    return query_db(query + ' ORDER BY created_at DESC', tuple(params))


def fetch_all_tickets(filters=None):
    filters = filters or {}
    query = 'SELECT t.*, u.fullname AS employee_name FROM tickets t JOIN users u ON t.employee_id = u.id WHERE 1=1'
    params = []

    if filters.get('category'):
        query += ' AND category = ?'
        params.append(filters['category'])
    if filters.get('status'):
        query += ' AND status = ?'
        params.append(filters['status'])
    if filters.get('priority'):
        query += ' AND priority = ?'
        params.append(filters['priority'])
    if filters.get('severity'):
        query += ' AND severity = ?'
        params.append(filters['severity'])
    if filters.get('assigned_to'):
        query += ' AND assigned_to = ?'
        params.append(filters['assigned_to'])
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        query += ' AND (CAST(t.id AS TEXT) LIKE ? OR t.title LIKE ? OR u.fullname LIKE ? OR t.category LIKE ? OR t.priority LIKE ? OR t.status LIKE ?)'
        params.extend([search_term] * 6)

    return query_db(query + ' ORDER BY updated_at DESC', tuple(params))


def get_ticket(ticket_id):
    return query_db('SELECT * FROM tickets WHERE id = ?', (ticket_id,), one=True)


def get_ticket_comments(ticket_id):
    return query_db(
        'SELECT c.*, u.fullname FROM comments c JOIN users u ON c.user_id = u.id WHERE c.ticket_id = ? ORDER BY c.created_at DESC',
        (ticket_id,)
    )


def get_ticket_activities(ticket_id):
    return query_db(
        'SELECT a.*, u.fullname FROM activities a JOIN users u ON a.created_by = u.id WHERE a.ticket_id = ? ORDER BY a.created_at DESC',
        (ticket_id,)
    )


def add_comment(ticket_id, user_id, comment):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO comments (ticket_id, user_id, comment, created_at) VALUES (?, ?, ?, ?)',
        (ticket_id, user_id, comment, timestamp)
    )
    conn.commit()
    conn.close()
    log_activity(ticket_id, user_id, 'Comment added')


def update_ticket_status(ticket_id, status, user_id):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    conn.execute(
        'UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?',
        (status, timestamp, ticket_id)
    )
    conn.commit()
    conn.close()
    log_activity(ticket_id, user_id, f'Status updated to {status}')


def assign_ticket(ticket_id, assignee_id, user_id):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    conn.execute(
        'UPDATE tickets SET assigned_to = ?, updated_at = ? WHERE id = ?',
        (assignee_id or None, timestamp, ticket_id)
    )
    conn.commit()
    conn.close()
    assignee = get_user_by_id(assignee_id) if assignee_id else None
    message = f"Assigned to {assignee['fullname']}" if assignee else 'Assignment removed'
    log_activity(ticket_id, user_id, message)


def add_resolution_notes(ticket_id, notes, user_id):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    conn.execute(
        'UPDATE tickets SET resolution_notes = ?, updated_at = ? WHERE id = ?',
        (notes, timestamp, ticket_id)
    )
    conn.commit()
    conn.close()
    log_activity(ticket_id, user_id, 'Resolution notes updated')


def log_activity(ticket_id, created_by, description):
    timestamp = datetime.utcnow().isoformat()
    conn = get_connection()
    conn.execute(
        'INSERT INTO activities (ticket_id, description, created_by, created_at) VALUES (?, ?, ?, ?)',
        (ticket_id, description, created_by, timestamp)
    )
    conn.commit()
    conn.close()


def ticket_stats_for_employee(employee_id):
    rows = query_db(
        'SELECT status, COUNT(*) AS count FROM tickets WHERE employee_id = ? GROUP BY status',
        (employee_id,)
    )
    return {row['status']: row['count'] for row in rows}


def dashboard_metrics():
    stats = query_db(
        'SELECT status, COUNT(*) AS count FROM tickets GROUP BY status'
    )
    categories = query_db(
        'SELECT category, COUNT(*) AS count FROM tickets GROUP BY category'
    )
    priorities = query_db(
        'SELECT priority, COUNT(*) AS count FROM tickets GROUP BY priority'
    )
    critical = query_db(
        "SELECT COUNT(*) AS count FROM tickets WHERE priority = 'Critical' OR severity = 'Critical'", (), one=True)

    return {
        'status': {row['status']: row['count'] for row in stats},
        'category': {row['category']: row['count'] for row in categories},
        'priority': {row['priority']: row['count'] for row in priorities},
        'critical': critical['count'] if critical else 0
    }
