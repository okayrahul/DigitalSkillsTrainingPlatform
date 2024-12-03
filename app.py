from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USER_DB = 'users.csv'
STUDENT_DB = 'students.csv'
PROGRESS_DB = 'progress.csv'
ATTENDANCE_DB = 'attendance.csv'
MODULE_DB = 'modules.csv'

# Create CSV files if they don't exist
def create_csv_file(file_path, header):
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

create_csv_file(USER_DB, ['name', 'username', 'password', 'role'])
create_csv_file(STUDENT_DB, ['student_id', 'name', 'date_of_birth', 'gender', 'enrollment_date', 'additional_info', 'grade_level'])
create_csv_file(PROGRESS_DB, ['student_id', 'module_id', 'status', 'last_updated'])
create_csv_file(ATTENDANCE_DB, ['student_id', 'date', 'status'])
create_csv_file(MODULE_DB, ['module_id', 'grade_level', 'subject', 'name', 'description', 'order'])

# Helper functions
def get_user(username):
    with open(USER_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['username'] == username:
                return user
    return None

def get_all_students():
    students = []
    with open(STUDENT_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        students = list(reader)
    return students

def get_student(student_id):
    with open(STUDENT_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for student in reader:
            if student['student_id'] == student_id:
                return student
    return None

def get_all_modules():
    modules = []
    with open(MODULE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        modules = list(reader)
    return modules

def get_modules_by_grade(grade_level):
    modules = []
    with open(MODULE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for module in reader:
            if module['grade_level'] == str(grade_level):
                modules.append(module)
    return modules

def get_student_progress(student_id):
    progress = {}
    with open(PROGRESS_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record['student_id'] == student_id:
                progress[record['module_id']] = record['status']
    return progress

def update_progress_record(student_id, module_id, status):
    records = []
    found = False
    if os.path.exists(PROGRESS_DB):
        with open(PROGRESS_DB, 'r', newline='') as f:
            reader = csv.DictReader(f)
            records = list(reader)

    for record in records:
        if record['student_id'] == student_id and record['module_id'] == module_id:
            record['status'] = status
            record['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            found = True
            break

    if not found:
        records.append({
            'student_id': student_id,
            'module_id': module_id,
            'status': status,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        })

    with open(PROGRESS_DB, 'w', newline='') as f:
        fieldnames = ['student_id', 'module_id', 'status', 'last_updated']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def get_attendance_by_date(date):
    attendance_records = []
    with open(ATTENDANCE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record['date'] == date:
                attendance_records.append(record)
    return attendance_records

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user(username)

        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['role'] = user['role']
            session['name'] = user['name']

            flash('You have been logged in successfully.', 'success')

            # Redirect based on role
            if user['role'] == 'instructor':
                return redirect(url_for('instructor_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/instructor-signup', methods=['GET', 'POST'])
def instructor_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        role = 'instructor'

        # Check if username already exists
        if get_user(username):
            flash('Username already exists. Please choose another.', 'error')
            return render_template('instructor_signup.html')

        # Add user to the USER_DB
        with open(USER_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, username, hashed_password, role])

        flash('Instructor account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('instructor_signup.html')

@app.route('/instructor-dashboard')
def instructor_dashboard():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    students = get_all_students()
    return render_template('instructor_dashboard.html', students=students)

@app.route('/students')
def students():
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    students = get_all_students()
    return render_template('students.html', students=students)

@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_id = str(uuid.uuid4())
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        enrollment_date = datetime.now().strftime('%Y-%m-%d')
        additional_info = request.form.get('additional_info', '')
        grade_level = request.form['grade_level']

        with open(STUDENT_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([student_id, name, date_of_birth, gender, enrollment_date, additional_info, grade_level])

        flash('Student added successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html')

@app.route('/assess-student/<student_id>', methods=['GET', 'POST'])
def assess_student(student_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    student = get_student(student_id)

    if request.method == 'POST':
        new_grade_level = request.form['grade_level']

        # Update student record
        students = get_all_students()
        for s in students:
            if s['student_id'] == student_id:
                s['grade_level'] = new_grade_level
                break

        # Write updated students back to file
        with open(STUDENT_DB, 'w', newline='') as f:
            fieldnames = ['student_id', 'name', 'date_of_birth', 'gender', 'enrollment_date', 'additional_info', 'grade_level']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(students)

        flash('Student grade level updated successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('assess_student.html', student=student)

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    students = get_all_students()
    date = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        date = request.form['date']
        for student in students:
            status = request.form.get(student['student_id'], 'Absent')
            with open(ATTENDANCE_DB, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([student['student_id'], date, status])

        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('attendance'))

    return render_template('attendance.html', students=students, date=date)

@app.route('/view-attendance')
def view_attendance():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    # Implement logic to view attendance records
    return render_template('view_attendance.html')

@app.route('/update-progress/<student_id>', methods=['GET', 'POST'])
def update_progress(student_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    student = get_student(student_id)
    grade_level = student['grade_level']
    modules = get_modules_by_grade(grade_level)
    student_progress = get_student_progress(student_id)

    if request.method == 'POST':
        for module in modules:
            status = request.form.get(module['module_id'], 'Not Started')
            update_progress_record(student_id, module['module_id'], status)

        flash('Progress updated successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('update_progress.html', student=student, modules=modules, progress=student_progress)

@app.route('/view-progress/<student_id>')
def view_progress(student_id):
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    student = get_student(student_id)
    grade_level = student['grade_level']
    modules = get_modules_by_grade(grade_level)
    student_progress = get_student_progress(student_id)

    return render_template('view_progress.html', student=student, modules=modules, progress=student_progress)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        flash('Please log in as an admin.', 'error')
        return redirect(url_for('login'))

    # Admin dashboard logic
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
