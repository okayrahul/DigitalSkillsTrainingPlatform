from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File to store user data
USER_DB = 'users.csv'

# Create users.csv if it doesn't exist
if not os.path.exists(USER_DB):
    with open(USER_DB, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'username', 'password'])

def get_user(username):
    with open(USER_DB, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['username'] == username:
                return user
    return None

@app.route('/')
def index():
    return render_template('landing_pg.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        if get_user(username):
            flash('Username already exists. Please choose another.', 'error')
            return render_template('signup.html')
        
        # Hash password before storing
        hashed_password = generate_password_hash(password)
        
        # Store new user in CSV
        with open(USER_DB, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, username, hashed_password])
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = get_user(username)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('courses'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('signin.html')
            
    return render_template('signin.html')


@app.route('/signout')
def signout():
    # Clear the user's session
    session.pop('user', None)
    flash('You have been signed out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/courses')
def courses():
    if 'user' in session:
        courses_list = [
            {'id': 1, 'title': 'Introduction to Python', 'description': 'Learn the basics of Python'},
            {'id': 2, 'title': 'Web Development with Flask', 'description': 'Build web applications using Flask'},
            {'id': 3, 'title': 'Data Analysis with Pandas', 'description': 'Analyze data with Python Pandas library'}
        ]
        return render_template('courses.html', courses=courses_list)
    else:
        return redirect(url_for('signin'))

@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course_content = {
        'title': 'Course Title',
        'description': 'Detailed description of the course.',
        'videos': ['video1.mp4', 'video2.mp4']
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

