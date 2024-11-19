from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USER_DB = 'users.csv'
COURSE_DB = 'courses.csv'
ENROLLMENTS_DB = 'enrollments.csv'
PROGRESS_DB = 'progress.csv'
ATTENDANCE_DB = 'attendance.csv'

# Create CSV files if they don't exist
for db_file, header in [
    (USER_DB, ['name', 'username', 'password', 'role']),
    (COURSE_DB, ['course_id', 'instructor_username', 'title', 'description']),
    (ENROLLMENTS_DB, ['course_id', 'student_username']),
    (PROGRESS_DB, ['course_id', 'student_username', 'progress_percentage']),
    (ATTENDANCE_DB, ['course_id', 'session_date', 'student_username', 'status']),
]:
    if not os.path.exists(db_file):
        with open(db_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

def get_user(username):
    with open(USER_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['username'] == username:
                return user
    return None

def get_instructor_courses(instructor_username):
    courses = []
    with open(COURSE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for course in reader:
            if course['instructor_username'] == instructor_username:
                courses.append(course)
    return courses

def get_student_courses(student_username):
    courses = []
    with open(ENROLLMENTS_DB, 'r', newline='') as f_enrollments, open(COURSE_DB, 'r', newline='') as f_courses:
        enrollments = list(csv.DictReader(f_enrollments))
        all_courses = list(csv.DictReader(f_courses))
        enrolled_course_ids = [e['course_id'] for e in enrollments if e['student_username'] == student_username]

        for course in all_courses:
            if course['course_id'] in enrolled_course_ids:
                courses.append(course)
    return courses


def get_enrolled_students(course_id):
    students = []
    with open(ENROLLMENTS_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for enrollment in reader:
            if enrollment['course_id'] == course_id:
                students.append(enrollment['student_username'])
    return students

def get_student_progress(course_id):
    progress_data = []
    with open(PROGRESS_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for progress in reader:
            if progress['course_id'] == course_id:
                progress_data.append(progress)
    return progress_data

def get_attendance_records(course_id):
    attendance = []
    with open(ATTENDANCE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record['course_id'] == course_id:
                attendance.append(record)
    return attendance

@app.route('/')
def index():
    return render_template('landing_pg.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Check if username already exists
        if get_user(username):
            flash('Username already exists. Please choose another.', 'error')
            return render_template('signup.html')

        # Hash password before storing
        hashed_password = generate_password_hash(password)

        # Store new user with role in CSV
        with open(USER_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, username, hashed_password, role])

        session['user'] = username
        session['role'] = role
        session['name'] = name

        flash('Registration successful! You are now logged in.', 'success')

        # Redirect based on role
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        elif role == 'instructor':
            return redirect(url_for('instructor_dashboard'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        selected_role = request.form['role']

        user = get_user(username)

        if user and check_password_hash(user['password'], password):
            # Verify if selected role matches user's actual role
            if user['role'] != selected_role:
                flash('Invalid role selected. Please try again.', 'error')
                return render_template('signin.html')

            # Set session variables
            session['user'] = username
            session['role'] = selected_role
            session['name'] = user['name']

            flash('You have been logged in successfully.', 'success')

            # Redirect based on role
            if selected_role == 'student':
                return redirect(url_for('student_dashboard'))
            elif selected_role == 'instructor':
                return redirect(url_for('instructor_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('signin.html')

    return render_template('signin.html')

@app.route('/signout')
def signout():
    session.pop('user', None)
    session.pop('role', None)
    session.pop('name', None)
    flash('You have been signed out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/student-dashboard')
def student_dashboard():
    if 'user' not in session or session['role'] != 'student':
        flash('Please log in as a student.', 'error')
        return redirect(url_for('signin'))

    courses = get_student_courses(session['user'])
    return render_template('student_dashboard.html', courses=courses)


@app.route('/instructor-dashboard')
def instructor_dashboard():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    courses = get_instructor_courses(session['user'])
    return render_template('instructor_dashboard.html', courses=courses)

@app.route('/create-course', methods=['GET', 'POST'])
def create_course():
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        course_id = str(uuid.uuid4())

        with open(COURSE_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([course_id, session['user'], title, description])

        flash('Course created successfully!', 'success')
        return redirect(url_for('instructor_dashboard'))

    return render_template('create_course.html')

@app.route('/edit-course/<course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    course = None
    with open(COURSE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        courses = list(reader)

    for c in courses:
        if c['course_id'] == course_id and c['instructor_username'] == session['user']:
            course = c
            break

    if not course:
        flash('Course not found or unauthorized access', 'error')
        return redirect(url_for('instructor_dashboard'))

    if request.method == 'POST':
        course['title'] = request.form['title']
        course['description'] = request.form['description']

        with open(COURSE_DB, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['course_id', 'instructor_username', 'title', 'description'])
            writer.writeheader()
            writer.writerows(courses)

        flash('Course updated successfully!', 'success')
        return redirect(url_for('instructor_dashboard'))

    return render_template('edit_course.html', course=course)

@app.route('/delete-course/<course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    with open(COURSE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        courses = list(reader)

    courses = [c for c in courses if not (c['course_id'] == course_id and c['instructor_username'] == session['user'])]

    with open(COURSE_DB, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['course_id', 'instructor_username', 'title', 'description'])
        writer.writeheader()
        writer.writerows(courses)

    flash('Course deleted successfully!', 'success')
    return redirect(url_for('instructor_dashboard'))

@app.route('/course-students/<course_id>')
def course_students(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    students = get_enrolled_students(course_id)
    return render_template('course_students.html', students=students, course_id=course_id)

@app.route('/enroll-student/<course_id>', methods=['GET', 'POST'])
def enroll_student(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    if request.method == 'POST':
        student_username = request.form['student_username']

        # Check if user exists and is a student
        student = get_user(student_username)
        if not student or student['role'] != 'student':
            flash('Student not found', 'error')
            return redirect(url_for('enroll_student', course_id=course_id))

        # Enroll student
        with open(ENROLLMENTS_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([course_id, student_username])

        flash('Student enrolled successfully!', 'success')
        return redirect(url_for('course_students', course_id=course_id))

    return render_template('enroll_student.html', course_id=course_id)

@app.route('/remove-student/<course_id>/<student_username>', methods=['POST'])
def remove_student(course_id, student_username):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    with open(ENROLLMENTS_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        enrollments = list(reader)

    enrollments = [e for e in enrollments if not (e['course_id'] == course_id and e['student_username'] == student_username)]

    with open(ENROLLMENTS_DB, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['course_id', 'student_username'])
        writer.writeheader()
        writer.writerows(enrollments)

    flash('Student removed successfully!', 'success')
    return redirect(url_for('course_students', course_id=course_id))

@app.route('/student-progress/<course_id>')
def student_progress(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    progress_data = get_student_progress(course_id)
    return render_template('student_progress.html', progress_data=progress_data, course_id=course_id)

@app.route('/mark-attendance/<course_id>', methods=['GET', 'POST'])
def mark_attendance(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    students = get_enrolled_students(course_id)

    if request.method == 'POST':
        attendance_records = []
        for student_username in students:
            status = request.form.get(student_username)
            attendance_records.append({
                'course_id': course_id,
                'session_date': datetime.now().strftime('%Y-%m-%d'),
                'student_username': student_username,
                'status': status
            })

        with open(ATTENDANCE_DB, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['course_id', 'session_date', 'student_username', 'status'])
            writer.writeheader()
            for record in attendance_records:
                writer.writerow(record)

        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('course_students', course_id=course_id))

    return render_template('mark_attendance.html', students=students, course_id=course_id)

@app.route('/attendance-records/<course_id>')
def attendance_records(course_id):
    if 'user' not in session or session['role'] != 'instructor':
        flash('Please login as an instructor', 'error')
        return redirect(url_for('signin'))

    attendance = get_attendance_records(course_id)
    return render_template('attendance_records.html', attendance=attendance, course_id=course_id)

@app.route('/courses')
def courses():
    if 'user' in session and session['role'] == 'student':
        # Get IDs of courses the student is enrolled in
        enrolled_courses = get_student_courses(session['user'])
        enrolled_course_ids = [course['course_id'] for course in enrolled_courses]

        # Display all courses not yet enrolled in
        courses_list = []
        with open(COURSE_DB, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for course in reader:
                if course['course_id'] not in enrolled_course_ids:
                    courses_list.append(course)
        return render_template('courses.html', courses=courses_list)
    else:
        flash('Please log in as a student to view available courses.', 'error')
        return redirect(url_for('signin'))


@app.route('/enroll-in-course/<course_id>', methods=['POST'])
def enroll_in_course(course_id):
    if 'user' not in session or session['role'] != 'student':
        flash('Please log in as a student to enroll.', 'error')
        return redirect(url_for('signin'))

    # Check if already enrolled
    enrolled_courses = get_student_courses(session['user'])
    if any(course['course_id'] == course_id for course in enrolled_courses):
        flash('You are already enrolled in this course.', 'error')
        return redirect(url_for('courses'))

    # Enroll the student
    with open(ENROLLMENTS_DB, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([course_id, session['user']])

    flash('You have successfully enrolled in the course!', 'success')
    return redirect(url_for('student_dashboard'))


@app.route('/courses/<course_id>')
def course_detail(course_id):
    # Fetch course details
    course = None
    with open(COURSE_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for c in reader:
            if c['course_id'] == course_id:
                course = c
                break

    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('courses'))

    course_content = {
        'title': course['title'],
        'description': course['description'],
        'videos': ['video1.mp4', 'video2.mp4']  # Placeholder for actual content
    }
    return render_template('course_detail.html', course=course_content)

@app.route('/profile')
def profile():
    if 'user' in session:
        # Display user profile information
        return render_template('profile.html', username=session['user'])
    else:
        return redirect(url_for('signin'))

if __name__ == '__main__':
    app.run(debug=True)
