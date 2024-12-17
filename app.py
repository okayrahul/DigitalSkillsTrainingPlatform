from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import csv
import os
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USER_DB = 'users.csv'
STUDENT_DB = 'students.csv'
PROGRESS_DB = 'progress.csv'
ATTENDANCE_DB = 'attendance.csv'
MODULE_DB = 'modules.csv'
ACTIVITIES_DB = 'activities.csv'
GRADES_DB = 'grades.csv'

BOOKS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/Books')

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
if not os.path.exists(ACTIVITIES_DB):
    create_csv_file(ACTIVITIES_DB, ['activity_id', 'activity_name', 'activity_description', 'date', 'grade_level'])
if not os.path.exists(GRADES_DB):
    create_csv_file(GRADES_DB, ['activity_id', 'student_id', 'grade', 'comments', 'date_assigned'])

def get_user(username):
    with open(USER_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['username'] == username:
                return user
    return None

def get_all_students():
    with open(STUDENT_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_student(student_id):
    with open(STUDENT_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for student in reader:
            if student['student_id'] == student_id:
                return student
    return None

def get_all_modules():
    with open(MODULE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_modules_by_grade(grade_level):
    with open(MODULE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return [m for m in reader if m['grade_level'] == str(grade_level)]

def get_student_progress(student_id):
    progress = {}
    with open(PROGRESS_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record['student_id'] == student_id:
                progress[record['module_id']] = {
                    'status': record['status'],
                    'last_updated': record['last_updated']
                }
    return progress

def get_attendance_by_student(student_id):
    attendance_records = {}
    with open(ATTENDANCE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record['student_id'] == student_id:
                attendance_records[record['date']] = record['status']
    return attendance_records

def get_activities_by_grade(grade_level):
    activities = []
    with open(ACTIVITIES_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for a in reader:
            if a['grade_level'] == str(grade_level):
                activities.append(a)
    return activities

def get_grades_for_student(student_id):
    grades = {}
    with open(GRADES_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for g in reader:
            if g['student_id'] == student_id:
                grades[g['activity_id']] = {
                    'grade': g['grade'],
                    'comments': g.get('comments', ''),
                    'date_assigned': g.get('date_assigned', '')
                }
    return grades

def extract_grade_level(filename):
    return filename.split('_')[1]

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

        if get_user(username):
            flash('Username already exists. Please choose another.', 'error')
            return render_template('instructor_signup.html')

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

@app.route('/edit-student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    student = get_student(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('students'))

    if request.method == 'POST':
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        grade_level = request.form['grade_level']
        additional_info = request.form.get('additional_info', '')

        all_students = get_all_students()
        for s in all_students:
            if s['student_id'] == student_id:
                s['name'] = name
                s['date_of_birth'] = date_of_birth
                s['gender'] = gender
                s['grade_level'] = grade_level
                s['additional_info'] = additional_info
                break

        fieldnames = ['student_id', 'name', 'date_of_birth', 'gender', 'enrollment_date', 'additional_info', 'grade_level']
        with open(STUDENT_DB, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_students)

        flash('Student information updated successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)

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

@app.route('/view-progress/<student_id>')
def view_progress(student_id):
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    student = get_student(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('students'))

    grade_level = student['grade_level']
    modules = get_modules_by_grade(grade_level)
    student_progress = get_student_progress(student_id)
    attendance_records = get_attendance_by_student(student_id)
    activities = get_activities_by_grade(grade_level)
    student_grades = get_grades_for_student(student_id)

    activity_data = []
    for activity in activities:
        activity_id = activity['activity_id']
        activity_date = activity['date']
        presence = attendance_records.get(activity_date, 'Absent')
        grade_info = student_grades.get(activity_id, {'grade': 'N/A', 'comments': ''})
        activity_data.append({
            'activity_name': activity['activity_name'],
            'activity_date': activity_date,
            'grade_level': activity['grade_level'],
            'presence': presence,
            'grade': grade_info['grade'],
            'comments': grade_info['comments']
        })

    status_counts = {'Not Started': 0, 'In Progress': 0, 'Completed': 0}
    if modules:
        for module in modules:
            mod_id = module['module_id']
            mod_status = student_progress.get(mod_id, {}).get('status', 'Not Started')
            if mod_status not in status_counts:
                status_counts[mod_status] = 0
            status_counts[mod_status] += 1

    return render_template(
        'view_progress.html',
        student=student,
        modules=modules,
        progress=student_progress,
        attendance=attendance_records,
        activities=activity_data,
        status_counts=status_counts
    )

@app.route('/delete-student/<student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user' not in session or session['role'] not in ['instructor', 'admin']:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    # Remove student from STUDENT_DB
    all_students = get_all_students()
    all_students = [s for s in all_students if s['student_id'] != student_id]
    fieldnames = ['student_id', 'name', 'date_of_birth', 'gender', 'enrollment_date', 'additional_info', 'grade_level']
    with open(STUDENT_DB, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_students)

    # Remove student's attendance records
    if os.path.exists(ATTENDANCE_DB):
        with open(ATTENDANCE_DB, 'r', newline='') as f:
            reader = csv.DictReader(f)
            attendance_records = [row for row in reader if row['student_id'] != student_id]
        with open(ATTENDANCE_DB, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['student_id','date','status'])
            writer.writeheader()
            writer.writerows(attendance_records)

    # Remove student's progress records
    if os.path.exists(PROGRESS_DB):
        with open(PROGRESS_DB, 'r', newline='') as f:
            reader = csv.DictReader(f)
            progress_records = [row for row in reader if row['student_id'] != student_id]
        with open(PROGRESS_DB, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['student_id','module_id','status','last_updated'])
            writer.writeheader()
            writer.writerows(progress_records)

    # Remove student's grades
    if os.path.exists(GRADES_DB):
        with open(GRADES_DB, 'r', newline='') as f:
            reader = csv.DictReader(f)
            grade_records = [row for row in reader if row['student_id'] != student_id]
        with open(GRADES_DB, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['activity_id','student_id','grade','comments','date_assigned'])
            writer.writeheader()
            writer.writerows(grade_records)

    flash('Student and related records deleted successfully!', 'success')
    return redirect(url_for('students'))

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        flash('Please log in as an admin.', 'error')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/view-attendance', methods=['GET'])
def view_attendance():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    students_df = pd.read_csv(STUDENT_DB)
    attendance_df = pd.read_csv(ATTENDANCE_DB)

    merged_data = pd.merge(
        attendance_df,
        students_df[['student_id', 'name']],
        on='student_id',
        how='left'
    )
    pivot_table = merged_data.pivot_table(
        index='name',
        columns='date',
        values='status',
        aggfunc=lambda x: '✔' if 'Present' in x.values else '✘',
        fill_value='✘'
    )
    pivot_table.reset_index(inplace=True)

    formatted_columns = ['name']
    for col in pivot_table.columns[1:]:
        try:
            date_obj = datetime.strptime(col, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d-%m-%Y')
            formatted_columns.append(formatted_date)
        except ValueError:
            formatted_columns.append(col)
    pivot_table.columns = formatted_columns

    attendance_table = {
        'columns': list(pivot_table.columns),
        'rows': pivot_table.to_dict(orient='records')
    }

    selected_date = request.args.get('date', None)
    return render_template(
        'view_attendance.html',
        attendance_table=attendance_table,
        selected_date=selected_date
    )

@app.route('/activities', methods=['GET', 'POST'])
def activities():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        activity_id = str(uuid.uuid4())
        activity_name = request.form['activity_name']
        activity_description = request.form['activity_description']
        activity_date = request.form['activity_date']
        activity_grade = request.form['grade_level']

        with open(ACTIVITIES_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([activity_id, activity_name, activity_description, activity_date, activity_grade])

        flash('Activity added successfully!', 'success')
        return redirect(url_for('activities'))

    act_list = []
    if os.path.exists(ACTIVITIES_DB):
        with open(ACTIVITIES_DB, 'r') as f:
            reader = csv.DictReader(f)
            act_list = list(reader)

    return render_template('activities.html', activities=act_list)

@app.route('/assign-grades/<activity_id>', methods=['GET', 'POST'])
def assign_grades(activity_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please log in as an instructor.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            new_grades = []
            if os.path.exists(GRADES_DB):
                with open(GRADES_DB, 'r') as f:
                    reader = csv.DictReader(f)
                    existing_grades = [row for row in reader if row['activity_id'] != activity_id]
            else:
                existing_grades = []

            for key, value in request.form.items():
                if key.startswith('grade_'):
                    student_id = key.replace('grade_', '')
                    grade = value
                    comments = request.form.get(f'comments_{student_id}', '')
                    new_grades.append({
                        'activity_id': activity_id,
                        'student_id': student_id,
                        'grade': grade,
                        'comments': comments,
                        'date_assigned': datetime.now().strftime('%Y-%m-%d')
                    })

            existing_grades.extend(new_grades)

            fieldnames = ['activity_id', 'student_id', 'grade', 'comments', 'date_assigned']
            with open(GRADES_DB, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(existing_grades)

            flash('Grades saved successfully!', 'success')
            return redirect(url_for('activities'))

        except Exception as e:
            flash(f'Error saving grades: {str(e)}', 'error')
            return redirect(url_for('assign_grades', activity_id=activity_id))

    activity = None
    with open(ACTIVITIES_DB, 'r') as f:
        reader = csv.DictReader(f)
        for a in reader:
            if a['activity_id'] == activity_id:
                activity = a
                break

    if not activity:
        flash('Activity not found.', 'error')
        return redirect(url_for('activities'))

    all_students = get_all_students()
    matching_students = [
        student for student in all_students
        if student['grade_level'] == activity['grade_level']
    ]

    existing_grades = {}
    if os.path.exists(GRADES_DB):
        with open(GRADES_DB, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['activity_id'] == activity_id:
                    existing_grades[row['student_id']] = {
                        'grade': row['grade'],
                        'comments': row.get('comments', '')
                    }

    if existing_grades:
        flash('Grades already exist for this activity. You can update them below.', 'info')

    return render_template(
        'assign_grades.html',
        activity=activity,
        students=matching_students,
        existing_grades=existing_grades
    )

@app.route('/resources')
def resources():
    if 'user' not in session:
        return redirect(url_for('login'))

    pdf_files = []
    if os.path.exists(BOOKS_FOLDER):
        for filename in os.listdir(BOOKS_FOLDER):
            if filename.endswith('.pdf'):
                pdf_files.append({
                    'filename': filename,
                    'description': filename.replace('.pdf', '').replace('_', ' ').title(),
                    'grade_level': extract_grade_level(filename)
                })

    return render_template('resources.html', resources=pdf_files)

@app.route('/download/<filename>')
def download_resource(filename):
    if 'user' not in session:
        return redirect(url_for('login'))
    return send_from_directory(BOOKS_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
