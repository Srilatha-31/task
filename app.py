from flask import Flask, render_template, request, redirect, session
from db import get_db_connection
from datetime import date

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- AUTH ---------------- #

@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            (name,email,password,role)
        )
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- DASHBOARD ---------------- #

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session['role'] == 'admin':
        cursor.execute("""
            SELECT tasks.*, users.name AS assigned_user
            FROM tasks
            JOIN users ON tasks.assigned_to = users.id
        """)
    else:
        cursor.execute("""
            SELECT tasks.*, users.name AS assigned_user
            FROM tasks
            JOIN users ON tasks.assigned_to = users.id
            WHERE assigned_to = %s
        """, (session['user_id'],))

    tasks = cursor.fetchall()

    today = date.today()

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Done'])
    pending = len([t for t in tasks if t['status'] != 'Done'])
    overdue = len([t for t in tasks if t['deadline'] and t['deadline'] < today])

    conn.close()

    return render_template('dashboard.html',
                           tasks=tasks,
                           total=total,
                           completed=completed,
                           pending=pending,
                           overdue=overdue,
                           role=session['role'])

# ---------------- PROJECT ---------------- #

@app.route('/create_project', methods=['GET','POST'])
def create_project():
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # GET request → show users
    if request.method == 'GET':
        cursor.execute("SELECT id, name FROM users")
        users = cursor.fetchall()
        conn.close()
        return render_template('create_project.html', users=users)

    # POST request → create project
    if request.method == 'POST':
        name = request.form['name']
        members = request.form.getlist('members')  # list of selected users

        # Insert project
        cursor.execute(
            "INSERT INTO projects (name, created_by) VALUES (%s, %s)",
            (name, session['user_id'])
        )

        # Get project ID
        project_id = cursor.lastrowid

        # Add creator as member
        cursor.execute(
            "INSERT INTO project_members (user_id, project_id) VALUES (%s, %s)",
            (session['user_id'], project_id)
        )

        # Add selected members
        for member in members:
            cursor.execute(
                "INSERT INTO project_members (user_id, project_id) VALUES (%s, %s)",
                (member, project_id)
            )

        conn.commit()
        conn.close()

        return redirect('/dashboard')

# ---------------- TASK ---------------- #

@app.route('/create_task', methods=['GET','POST'])
def create_task():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- GET ---------------- #
    if request.method == 'GET':
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()

        # Initially show all users (before selecting project)
        cursor.execute("SELECT id, name FROM users")
        users = cursor.fetchall()

        conn.close()
        return render_template('create_task.html', users=users, projects=projects)

    # ---------------- POST ---------------- #
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        deadline = request.form['deadline']
        assigned_to = request.form['assigned_to']
        project_id = request.form['project_id']
        priority = request.form['priority']   # ✅ NEW

        cursor.execute("""
            INSERT INTO tasks 
            (title, description, deadline, assigned_to, project_id, priority)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (title, desc, deadline, assigned_to, project_id, priority))

        conn.commit()
        conn.close()

        return redirect('/dashboard')


# ---------------- UPDATE STATUS ---------------- #

@app.route('/update_status/<int:id>')
def update_status(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks 
        SET status = CASE 
            WHEN status='Pending' THEN 'In Progress'
            WHEN status='In Progress' THEN 'Done'
            ELSE 'Done'
        END
        WHERE id=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- RUN ---------------- #

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)