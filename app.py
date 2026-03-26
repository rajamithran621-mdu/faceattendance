from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import base64
import csv
import io
from datetime import datetime
from functools import wraps
from database import (
    init_db, create_student, get_student_by_email, get_student_by_id,
    create_staff, get_staff_by_email, get_staff_by_id,
    get_all_students, update_student_face, delete_student, update_student,
    mark_attendance, get_student_attendance, get_attendance_percentage,
    get_subject_wise_attendance, get_daily_report, get_weekly_report,
    get_present_absent_lists, get_subjects, get_dashboard_stats
)
from face_engine import save_face_image, train_model, recognize_face

app = Flask(__name__)
app.secret_key = 'face_attendance_secret_key_2026'

# ─── Auth Decorators ──────────────────────────────────────────────

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'staff':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Public Routes ────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('staff_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        if role == 'student':
            user = get_student_by_email(email)
        else:
            user = get_staff_by_email(email)

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = role
            if role == 'student':
                session['roll_no'] = user['roll_no']
                session['department'] = user['department']
                return redirect(url_for('student_dashboard'))
            else:
                session['department'] = user['department']
                return redirect(url_for('staff_dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        department = request.form.get('department', 'CSE')

        if role == 'student':
            roll_no = request.form.get('roll_no', '').strip()
            success = create_student(name, email, password, roll_no, department)
            if success:
                user = get_student_by_email(email)
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['role'] = 'student'
                session['roll_no'] = user['roll_no']
                session['department'] = user['department']
                return redirect(url_for('capture_face'))
            else:
                return render_template('register.html', error='Email or Roll No already exists')
        else:
            success = create_staff(name, email, password, department)
            if success:
                user = get_staff_by_email(email)
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['role'] = 'staff'
                session['department'] = user['department']
                return redirect(url_for('staff_dashboard'))
            else:
                return render_template('register.html', error='Email already exists')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Face Capture ─────────────────────────────────────────────────

@app.route('/capture-face')
@student_required
def capture_face():
    return render_template('capture_face.html')

@app.route('/api/save-face', methods=['POST'])
@student_required
def api_save_face():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'No image data'}), 400

    image_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
    image_bytes = base64.b64decode(image_b64)

    student_id = session['user_id']
    img_path = save_face_image(student_id, image_bytes)

    if img_path:
        update_student_face(student_id, img_path)
        train_model()
        return jsonify({'success': True, 'message': 'Face saved and model trained!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to save face image'}), 500

# ─── Student Dashboard ────────────────────────────────────────────

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session['user_id']
    percentage = get_attendance_percentage(student_id)
    subject_attendance = get_subject_wise_attendance(student_id)
    recent_records = get_student_attendance(student_id)[:20]
    is_danger = percentage < 75

    return render_template('student_dashboard.html',
        percentage=percentage,
        subject_attendance=subject_attendance,
        recent_records=recent_records,
        is_danger=is_danger
    )

# ─── Staff Dashboard ──────────────────────────────────────────────

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    today = datetime.now().strftime('%Y-%m-%d')
    daily = get_daily_report(today, session['user_id'])
    present, absent = get_present_absent_lists(today)
    all_students = get_all_students()
    subjects = get_subjects()
    stats = get_dashboard_stats()

    return render_template('staff_dashboard.html',
        daily_report=daily,
        present_list=present,
        absent_list=absent,
        total_students=len(all_students),
        present_count=len(present),
        absent_count=len(absent),
        subjects=subjects,
        today=today,
        stats=stats
    )

# ─── Take Attendance (Camera) ────────────────────────────────────

@app.route('/staff/take-attendance')
@staff_required
def take_attendance():
    subjects = get_subjects()
    return render_template('take_attendance.html', subjects=subjects)

@app.route('/api/recognize', methods=['POST'])
@staff_required
def api_recognize():
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'No image data'}), 400

    image_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
    image_bytes = base64.b64decode(image_b64)
    subject = data.get('subject', 'General')

    student_id, confidence = recognize_face(image_bytes)

    if student_id:
        student = get_student_by_id(student_id)
        if student:
            marked = mark_attendance(student_id, session['user_id'], subject)
            return jsonify({
                'success': True,
                'student_name': student['name'],
                'roll_no': student['roll_no'],
                'department': student['department'],
                'confidence': round(confidence, 2),
                'already_marked': not marked,
                'message': f"{'Already marked' if not marked else 'Attendance marked'} for {student['name']}"
            })

    return jsonify({'success': False, 'message': 'Face not recognized. Please try again.'})

@app.route('/api/mark-attendance', methods=['POST'])
@staff_required
def api_mark_attendance():
    data = request.json
    student_id = data.get('student_id')
    subject = data.get('subject', 'General')
    status = data.get('status', 'present')

    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required'}), 400

    marked = mark_attendance(student_id, session['user_id'], subject, status)
    return jsonify({
        'success': True,
        'already_marked': not marked,
        'message': 'Attendance marked' if marked else 'Already marked for today'
    })

# ─── Reports API ──────────────────────────────────────────────────

@app.route('/api/report/daily')
@staff_required
def api_daily_report():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    records = get_daily_report(date, session['user_id'])
    present, absent = get_present_absent_lists(date)

    return jsonify({
        'records': [dict(r) for r in records],
        'present': [dict(p) for p in present],
        'absent': [dict(a) for a in absent],
        'date': date
    })

@app.route('/api/report/weekly')
@staff_required
def api_weekly_report():
    records = get_weekly_report(session['user_id'])
    return jsonify({
        'records': [dict(r) for r in records]
    })

@app.route('/api/report/download')
@staff_required
def api_download_report():
    report_type = request.args.get('type', 'daily')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    if report_type == 'daily':
        records = get_daily_report(date, session['user_id'])
    else:
        records = get_weekly_report(session['user_id'])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Roll No', 'Department', 'Date', 'Time', 'Status', 'Subject'])

    for r in records:
        writer.writerow([
            r['student_name'], r['roll_no'], r['department'],
            r['date'], r['time'], r['status'], r['subject']
        ])

    output.seek(0)
    bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))

    filename = f"attendance_{report_type}_{date}.csv"
    return send_file(bytes_output, mimetype='text/csv', as_attachment=True, download_name=filename)

@app.route('/api/students')
@staff_required
def api_students():
    students = get_all_students()
    return jsonify([dict(s) for s in students])

@app.route('/api/dashboard-stats')
@staff_required
def api_dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

# ─── Monthly Report Page ──────────────────────────────────────────

@app.route('/staff/reports')
@staff_required
def staff_reports():
    return render_template('monthly_report.html')

# ─── Monthly Report API ───────────────────────────────────────────

@app.route('/api/report/monthly')
@staff_required
def api_monthly_report():
    import calendar
    month = request.args.get('month', datetime.now().strftime('%m'))
    year  = request.args.get('year',  datetime.now().strftime('%Y'))
    dept  = request.args.get('dept', '')

    try:
        month_int = int(month)
        year_int  = int(year)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid month/year'}), 400

    month_str = f"{year_int}-{month_int:02d}"
    month_name = calendar.month_name[month_int]

    conn = __import__('database').get_db()

    query = '''
        SELECT a.date, a.time, a.status, a.subject,
               s.name as student_name, s.roll_no, s.department
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE strftime('%Y-%m', a.date) = ?
    '''
    params = [month_str]
    if dept:
        query += ' AND s.department = ?'
        params.append(dept)
    query += ' ORDER BY a.date, s.name'

    records = conn.execute(query, params).fetchall()
    conn.close()

    records_list = [dict(r) for r in records]

    days_in_month = calendar.monthrange(year_int, month_int)[1]
    daily_present = {}
    daily_absent  = {}

    for r in records_list:
        d = r['date']
        if r['status'] == 'present':
            daily_present[d] = daily_present.get(d, 0) + 1
        else:
            daily_absent[d] = daily_absent.get(d, 0) + 1

    all_days = sorted(set(list(daily_present.keys()) + list(daily_absent.keys())))
    labels   = [d[8:] for d in all_days]
    dp_vals  = [daily_present.get(d, 0) for d in all_days]
    da_vals  = [daily_absent.get(d, 0)  for d in all_days]
    pct_vals = [
        round((dp_vals[i] / (dp_vals[i] + da_vals[i])) * 100, 1)
        if (dp_vals[i] + da_vals[i]) > 0 else 0
        for i in range(len(all_days))
    ]

    total_present = sum(1 for r in records_list if r['status'] == 'present')
    total_absent  = sum(1 for r in records_list if r['status'] != 'present')
    total_records = len(records_list)
    pct = round((total_present / total_records) * 100, 1) if total_records > 0 else 0

    return jsonify({
        'success': True,
        'month_name': month_name,
        'year': year_int,
        'records': records_list,
        'daily_labels':     labels,
        'daily_present':    dp_vals,
        'daily_absent':     da_vals,
        'daily_percentage': pct_vals,
        'summary': {
            'total_working_days': len(all_days),
            'present_days':       total_present,
            'absent_days':        total_absent,
            'percentage':         pct,
        }
    })

@app.route('/api/report/monthly/csv')
@staff_required
def api_monthly_csv():
    month = request.args.get('month', datetime.now().strftime('%m'))
    year  = request.args.get('year',  datetime.now().strftime('%Y'))
    dept  = request.args.get('dept', '')

    month_str = f"{year}-{int(month):02d}"
    conn = __import__('database').get_db()
    query = '''
        SELECT a.date, a.time, a.status, a.subject,
               s.name as student_name, s.roll_no, s.department
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE strftime('%Y-%m', a.date) = ?
    '''
    params = [month_str]
    if dept:
        query += ' AND s.department = ?'; params.append(dept)
    query += ' ORDER BY a.date, s.name'
    records = conn.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student Name', 'Roll No', 'Department', 'Time', 'Status', 'Subject'])
    for r in records:
        writer.writerow([r['date'], r['student_name'], r['roll_no'], r['department'], r['time'], r['status'], r['subject']])

    output.seek(0)
    bytes_out = io.BytesIO(output.getvalue().encode('utf-8'))
    return send_file(bytes_out, mimetype='text/csv', as_attachment=True,
                     download_name=f"monthly_report_{year}_{month}.csv")

@app.route('/api/report/monthly/pdf')
@staff_required
def api_monthly_pdf():
    month = request.args.get('month', datetime.now().strftime('%m'))
    year  = request.args.get('year',  datetime.now().strftime('%Y'))
    import calendar
    month_name = calendar.month_name[int(month)]
    month_str  = f"{year}-{int(month):02d}"

    conn = __import__('database').get_db()
    records = conn.execute('''
        SELECT a.date, a.time, a.status, a.subject,
               s.name as student_name, s.roll_no, s.department
        FROM attendance a JOIN students s ON a.student_id = s.id
        WHERE strftime('%Y-%m', a.date) = ?
        ORDER BY a.date, s.name
    ''', [month_str]).fetchall()
    conn.close()

    total = len(records)
    present = sum(1 for r in records if r['status'] == 'present')
    pct = round((present / total) * 100, 1) if total > 0 else 0

    rows_html = ''.join(
        f"<tr><td>{r['date']}</td><td>{r['student_name']}</td><td>{r['roll_no']}</td>"
        f"<td>{r['department']}</td><td>{r['time']}</td><td>{r['status'].upper()}</td></tr>"
        for r in records
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>Attendance Report — {month_name} {year}</title>
    <style>
      body{{font-family:'Inter',Arial,sans-serif;background:#091413;color:#B0E4CC;padding:2rem}}
      h1{{font-size:1.4rem;margin-bottom:0.25rem;color:#B0E4CC}}
      p{{color:#408A71;font-size:0.85rem;margin-bottom:1.5rem}}
      .summary{{display:flex;gap:2rem;margin-bottom:1.5rem}}
      .s-box{{background:rgba(40,90,72,0.3);padding:1rem 1.5rem;border-radius:12px;text-align:center;border:1px solid rgba(64,138,113,0.2)}}
      .s-box strong{{display:block;font-size:1.6rem;font-weight:800;color:#B0E4CC}}
      .s-box span{{font-size:0.75rem;color:#408A71;text-transform:uppercase}}
      table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
      th{{background:rgba(40,90,72,0.4);color:#B0E4CC;padding:8px 12px;text-align:left;border:1px solid rgba(64,138,113,0.15)}}
      td{{padding:7px 12px;border-bottom:1px solid rgba(64,138,113,0.1);color:#B0E4CC}}
      tr:nth-child(even) td{{background:rgba(40,90,72,0.1)}}
      @media print{{body{{background:#fff;color:#111}} th{{background:#285A48;color:#fff}} td{{color:#111}} .s-box{{background:#f5f5f5;border-color:#ddd}} .s-box strong{{color:#111}} .s-box span{{color:#666}} h1{{color:#111}} p{{color:#555}}}}
    </style></head><body>
    <h1>📊 Attendance Report — {month_name} {year}</h1>
    <p>Generated by FaceAttend · Staff: {session.get('user_name','')}</p>
    <div class="summary">
      <div class="s-box"><strong>{total}</strong><span>Total Records</span></div>
      <div class="s-box"><strong>{present}</strong><span>Present</span></div>
      <div class="s-box"><strong>{total - present}</strong><span>Absent</span></div>
      <div class="s-box"><strong>{pct}%</strong><span>Attendance</span></div>
    </div>
    <table><thead><tr><th>Date</th><th>Student</th><th>Roll No</th><th>Dept</th><th>Time</th><th>Status</th></tr></thead>
    <tbody>{rows_html}</tbody></table>
    <script>window.onload=()=>window.print()</script>
    </body></html>"""

    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ─── User Management ─────────────────────────────────────────────

@app.route('/staff/users')
@staff_required
def staff_users():
    students = get_all_students()
    return render_template('users.html', students=students)

@app.route('/api/students/delete/<int:student_id>', methods=['POST'])
@staff_required
def api_delete_student(student_id):
    success = delete_student(student_id)
    if success:
        from face_engine import delete_face_images
        delete_face_images(student_id)
        train_model()
        return jsonify({'success': True, 'message': 'Student deleted'})
    return jsonify({'success': False, 'message': 'Failed to delete'}), 500

@app.route('/api/students/update/<int:student_id>', methods=['POST'])
@staff_required
def api_update_student(student_id):
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    department = data.get('department', '')
    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email required'}), 400
    success = update_student(student_id, name, email, department)
    if success:
        return jsonify({'success': True, 'message': 'Student updated'})
    return jsonify({'success': False, 'message': 'Email conflict'}), 400

# ─── Settings Page ────────────────────────────────────────────────

@app.route('/staff/settings')
@staff_required
def staff_settings():
    return render_template('settings.html')

# ─── Initialize & Run ────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    os.makedirs('faces', exist_ok=True)
    print("🎓 Face Recognition Attendance System")
    print("🌐 Running at http://localhost:5000")
    app.run(debug=True, port=5000)
