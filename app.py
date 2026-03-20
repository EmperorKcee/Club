from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from data_structures import StudentManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize the student manager
student_manager = StudentManager()

# Simple user credentials (in production, use a database with hashed passwords)
USERS = {
    'admin': 'admin123',
    'user': 'user123'
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    students = student_manager.get_all_students()
    queue_count = len(student_manager.get_registration_queue())
    return render_template('index.html', students=students, queue_count=queue_count)

@app.route('/students')
@login_required
def students():
    all_students = student_manager.get_all_students()
    return render_template('students.html', students=all_students)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        program = request.form['program']
        year = request.form['year']
        
        if student_manager.add_student(student_id, name, program, year):
            flash('Student added successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Student ID already exists!', 'error')
    
    return render_template('add_student.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_student():
    student = None
    if request.method == 'POST':
        student_id = request.form['student_id']
        student = student_manager.search_student(student_id)
        if not student:
            flash('Student not found!', 'error')
    
    return render_template('search_student.html', student=student)

@app.route('/update/<student_id>', methods=['GET', 'POST'])
@login_required
def update_student(student_id):
    if request.method == 'POST':
        name = request.form['name']
        program = request.form['program']
        year = request.form['year']
        
        if student_manager.update_student(student_id, name, program, year):
            flash('Student updated successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Student not found!', 'error')
    
    student = student_manager.search_student(student_id)
    return render_template('update_student.html', student=student)

@app.route('/delete/<student_id>')
@login_required
def delete_student(student_id):
    if student_manager.delete_student(student_id):
        flash('Student deleted successfully!', 'success')
    else:
        flash('Student not found!', 'error')
    return redirect(url_for('index'))

@app.route('/undo')
@login_required
def undo_delete():
    if student_manager.undo_delete():
        flash('Delete operation undone!', 'success')
    else:
        flash('No delete operation to undo!', 'error')
    return redirect(url_for('index'))

@app.route('/queue')
@login_required
def view_queue():
    queue_items = student_manager.get_registration_queue()
    return render_template('queue.html', queue_items=queue_items)

@app.route('/queue/add', methods=['POST'])
@login_required
def add_to_queue():
    student_id = request.form['student_id']
    student_manager.add_to_registration_queue(student_id)
    flash('Added to registration queue!', 'success')
    return redirect(url_for('view_queue'))

@app.route('/queue/process')
@login_required
def process_queue():
    processed = student_manager.process_registration_queue()
    if processed:
        flash(f'Processed registration for Student ID: {processed}', 'success')
    else:
        flash('Queue is empty!', 'error')
    return redirect(url_for('view_queue'))

if __name__ == '__main__':
    app.run(debug=True)
