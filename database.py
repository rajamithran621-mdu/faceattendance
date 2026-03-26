import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendance.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            face_image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            staff_id INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            subject TEXT DEFAULT 'General',
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id)
        );
    ''')

    # Seed default subjects
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        subjects = [
            ('Mathematics', 'CSE'), ('Data Structures', 'CSE'),
            ('Operating Systems', 'CSE'), ('Database Systems', 'CSE'),
            ('Computer Networks', 'CSE'), ('Web Development', 'CSE'),
            ('Physics', 'ECE'), ('Signals & Systems', 'ECE'),
            ('Digital Electronics', 'ECE'), ('Communication Systems', 'ECE'),
        ]
        cursor.executemany("INSERT INTO subjects (name, department) VALUES (?, ?)", subjects)

    conn.commit()
    conn.close()

# ─── Student Helpers ──────────────────────────────────────────────

def create_student(name, email, password, roll_no, department, face_image_path=None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO students (name, email, password, roll_no, department, face_image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, password, roll_no, department, face_image_path)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_student_by_email(email):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return student

def get_student_by_id(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return student

def get_all_students(department=None):
    conn = get_db()
    if department:
        students = conn.execute("SELECT * FROM students WHERE department = ? ORDER BY name", (department,)).fetchall()
    else:
        students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return students

def update_student_face(student_id, face_image_path):
    conn = get_db()
    conn.execute("UPDATE students SET face_image_path = ? WHERE id = ?", (face_image_path, student_id))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def update_student(student_id, name, email, department):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE students SET name = ?, email = ?, department = ? WHERE id = ?",
            (name, email, department, student_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ─── Staff Helpers ────────────────────────────────────────────────

def create_staff(name, email, password, department):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO staff (name, email, password, department) VALUES (?, ?, ?, ?)",
            (name, email, password, department)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_staff_by_email(email):
    conn = get_db()
    staff = conn.execute("SELECT * FROM staff WHERE email = ?", (email,)).fetchone()
    conn.close()
    return staff

def get_staff_by_id(staff_id):
    conn = get_db()
    staff = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
    conn.close()
    return staff

# ─── Attendance Helpers ───────────────────────────────────────────

def mark_attendance(student_id, staff_id, subject='General', status='present'):
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M:%S')

    existing = conn.execute(
        "SELECT * FROM attendance WHERE student_id = ? AND date = ? AND subject = ?",
        (student_id, today, subject)
    ).fetchone()

    if existing:
        conn.close()
        return False

    conn.execute(
        "INSERT INTO attendance (student_id, staff_id, date, time, status, subject) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, staff_id, today, now, status, subject)
    )
    conn.commit()
    conn.close()
    return True

def get_student_attendance(student_id):
    conn = get_db()
    records = conn.execute(
        "SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC",
        (student_id,)
    ).fetchall()
    conn.close()
    return records

def get_attendance_percentage(student_id):
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(DISTINCT date || subject) FROM attendance WHERE student_id = ?",
        (student_id,)
    ).fetchone()[0]

    present = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE student_id = ? AND status = 'present'",
        (student_id,)
    ).fetchone()[0]

    conn.close()

    if total == 0:
        return 100.0
    return round((present / total) * 100, 1)

def get_subject_wise_attendance(student_id):
    conn = get_db()
    results = conn.execute('''
        SELECT subject,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count
        FROM attendance
        WHERE student_id = ?
        GROUP BY subject
    ''', (student_id,)).fetchall()
    conn.close()
    return results

def get_daily_report(date=None, staff_id=None):
    conn = get_db()
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    query = '''
        SELECT a.*, s.name as student_name, s.roll_no, s.department
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
    '''
    params = [date]
    if staff_id:
        query += " AND a.staff_id = ?"
        params.append(staff_id)

    query += " ORDER BY s.name"
    records = conn.execute(query, params).fetchall()
    conn.close()
    return records

def get_weekly_report(staff_id=None):
    conn = get_db()
    today = datetime.now()
    week_start = (today - timedelta(days=6)).strftime('%Y-%m-%d')

    query = '''
        SELECT a.*, s.name as student_name, s.roll_no, s.department
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date >= ?
    '''
    params = [week_start]
    if staff_id:
        query += " AND a.staff_id = ?"
        params.append(staff_id)

    query += " ORDER BY a.date DESC, s.name"
    records = conn.execute(query, params).fetchall()
    conn.close()
    return records

def get_present_absent_lists(date=None):
    conn = get_db()
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    present = conn.execute('''
        SELECT DISTINCT s.id, s.name, s.roll_no, s.department
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        WHERE a.date = ? AND a.status = 'present'
        ORDER BY s.name
    ''', (date,)).fetchall()

    all_students = conn.execute("SELECT id, name, roll_no, department FROM students ORDER BY name").fetchall()

    present_ids = {row['id'] for row in present}
    absent = [s for s in all_students if s['id'] not in present_ids]

    conn.close()
    return present, absent

def get_subjects(department=None):
    conn = get_db()
    if department:
        subjects = conn.execute("SELECT * FROM subjects WHERE department = ?", (department,)).fetchall()
    else:
        subjects = conn.execute("SELECT * FROM subjects").fetchall()
    conn.close()
    return subjects

# ─── Dashboard Stats ──────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_db()
    today = datetime.now().strftime('%Y-%m-%d')

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    present_today = conn.execute(
        "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ? AND status = 'present'",
        (today,)
    ).fetchone()[0]

    absent_today = total_students - present_today

    all_attendance = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    all_present = conn.execute("SELECT COUNT(*) FROM attendance WHERE status = 'present'").fetchone()[0]
    overall_pct = round((all_present / all_attendance) * 100, 1) if all_attendance > 0 else 100.0

    # Weekly trend (last 7 days)
    week_labels = []
    week_present = []
    week_absent = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_name = (datetime.now() - timedelta(days=i)).strftime('%a')
        week_labels.append(day_name)

        p = conn.execute(
            "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ? AND status = 'present'", (d,)
        ).fetchone()[0]
        week_present.append(p)
        week_absent.append(total_students - p if total_students > 0 else 0)

    conn.close()
    return {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'overall_pct': overall_pct,
        'week_labels': week_labels,
        'week_present': week_present,
        'week_absent': week_absent,
    }
