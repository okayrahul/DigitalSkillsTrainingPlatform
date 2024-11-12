from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('landing_pg.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle sign up logic here
        # For now, we'll just redirect to signin
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle sign in logic
        session['user'] = request.form['username']
        return redirect(url_for('courses'))
    return render_template('signin.html')

@app.route('/signout')
def signout():
    session.pop('user', None)
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

if __name__ == '__main__':
    app.run(debug=True)
