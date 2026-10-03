from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
app = Flask(__name__)
app.secret_key = "supersecret123"

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       email TEXT UNIQUE NOT NULL,
                       password TEXT NOT NULL,
                       role TEXT NOT NULL   
                   )
                """)
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS connection_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        mentor_id INTEGER NOT NULL,
                        status TEXT NOT NULL
                   )
                """)
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS mentor_performance(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       mentor_id INTEGER,
                       subject TEXT,
                       specialization TEXT
                   )
                """)
    if "specialization" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN specialization TEXT")
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='mentor'")
        if cursor.fetchone()[0] ==0:
            cursor.execute("INSERT INTO users (name, email, password, role) VALUES ('Math Mentor', 'math@example.com', '123', 'mentor')")
            mentor_id = cursor.lastrowid
            cursor.execute("INSERT INTO mentor_performance (mentor_id, subject, specialization) VALUES (?, 'Mathematics', 'Algebra & Calculus')", (mentor_id,))
    conn.commit()
    conn.close()
init_db()

def create_test_users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    from werkzeug.security import generate_password_hash
    cursor.execute("DELETE FROM users")
    
    users_raw = [
        ("Student One", "student@example.com", "1234", "student"),
        ("Math Mentor", "math@example.com", "1234", "mentor"),
        ("Programming Mentor", "programming@example.com", "1234", "mentor"),
        ("Physics Mentor", "physics@example.com", "1234", "mentor")
    ]
    for name, email, pwd, role in users_raw:
        hashed = generate_password_hash(pwd)
        cursor.execute("INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", (name, email, hashed, role))
    cursor.execute(
        "UPDATE users SET specialization = ? WHERE email = ?",
        ("Mathematics", "math@example.com")
        )
    cursor.execute(
        "UPDATE users SET specialization = ? WHERE email = ?",
        ("Programming", "programming@example.com")
        )
    cursor.execute(
        "UPDATE users SET specialization = ? WHERE email = ?",
        ("Physics", "physics@example.com")
        )
        
    conn.commit()
    conn.close()
    
create_test_users()
        
connection_requests = []

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
       email = request.form["email"]
       password = request.form["password"]
       
       conn = sqlite3.connect("database.db")
       cursor = conn.cursor()
       cursor.execute(
           "SELECT id, name, email, password, role FROM users WHERE email = ? AND password = ?",
           (email, password)
       )
       user = cursor.fetchone()
       conn.close()
       
       if user:
           session["user_id"] = user[0]
           session["name"] = user[1]
           session["role"] = user[4]
           
           if user[4] == "mentor":
               return render_template("mentor_dashboard.html")
           return render_template("dashboard.html")
       return "Invalid email or password"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/performance")
def performance():
    grades = {
        "Mathematics": 45,
        "Programming": 72,
        "Physics": 58,
        "Computer Network": 80
    }
    return render_template("performance.html", grades=grades, gardes=grades) 

@app.route("/courses")
def courses():
    return render_template("courses.html") 

@app.route("/mentorship")
def mentorship():
    return render_template("mentorship.html") 

@app.route("/recommendations")
def recommendations():
    grades = {
        "Mathematics": 45,
        "Python": 38,
        "Physics": 42,
        "English": 65
    }
    recommendations= []
    for subject, grade in grades.items():
        if grade < 50:
            if subject == "Mathematics":
                recommendation = "Join a Math Mentorship Group."
            elif subject == "Python":
                recommendation = "Join a Programming Mentorship Group."
            elif subject == "Physics":
                recommendation = "Join a Science Mentorship Group."
            else:
                recommendation = "Join a Study Support Group."
                
            recommendations.append(
                f"{subject}: {recommendation}"
            )
            
    return render_template("recommendations.html", recommendations=recommendations)

@app.route("/connect", methods=["GET", "POST"])
def connect():
    if request.method == "POST":
        
        student_id = 2
        mentor_id = request.form.get("mentor_id")
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM connection_requests
            WHERE student_id = ? AND mentor_id = ?
        """, (student_id, mentor_id))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return "You have sent a request to this mentor"
        
        cursor.execute("""
            INSERT INTO connection_requests
            (student_id, mentor_id, status)
            VALUES (?, ?, ?)
            """, (student_id, mentor_id, 'pending'))
        
        conn.commit()
        conn.close()
        
        return "Connection request sent!"
    mentor_id = request.args.get("mentor_id")
    
    return render_template("connect.html", mentor_id=mentor_id)

@app.route("/requests")
def requests_page():
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cr.id, s.name, m.name, m.specialization, cr.status 
        FROM connection_requests cr
        JOIN users s ON cr.student_id = s.id
        JOIN users m ON cr.mentor_id = m.id
    """)
    connection_requests = cursor.fetchall()
    conn.close()
    return render_template("requests.html", connection_requests=connection_requests) 

@app.route("/accept-request", methods=["POST"])
def accept_request():
    request_id = request.form.get("request_id")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE connection_requests SET status = ? WHERE id = ?",
        ("Accepted", request_id)
    )
    conn.commit()
    conn.close()
        
    return "Connection request accepted!"

@app.route("/decline-request", methods=["POST"])
def decline_request():
    request_id = request.form.get("request_id")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE connection_requests SET status = ? WHERE id = ?",
        ("Declined", request_id)
    )
    conn.commit()
    conn.close()
    return "Connection request declined!"

@app.route("/users")
def users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    
    conn.close()
    return "<br>".join(
        f"ID: {user[0]} | Name: {user[1]} | Email: {user[2]} | Role: {user[3]}"
        for user in users
    )

@app.route("/my_requests")
def my_requests():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connection_requests WHERE student_id=2")
    requests = cursor.fetchall()
    conn.close()
    return render_template("my_requests.html",requests=requests)

@app.route("/connections")
def connections():
    student_id = 1
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                   SELECT u.name, u.specialization
                   FROM connection_requests cr
                   JOIN users u ON cr.mentor_id = u.id
                   WHERE cr.student_id = ? AND cr.status = "Accepted"
                   """, (student_id,))
    connections = cursor.fetchall()
    conn.close()
    return render_template("connections.html", connections=connections)

@app.route("/mentor_connections")
def mentor_connections():
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                SELECT s.name, m.name, m.specialization
                FROM connection_requests cr
                JOIN users s ON cr.student_id = s.id
                JOIN users m ON cr.mentor_id = m.id
                WHERE cr.status = "Accepted"
                """)
    connections = cursor.fetchall()
    conn.close()
    return render_template("mentor_connections.html", connections=connections)

@app.route("/connected_students")
def connected_students():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
                SELECT s.id, s.name, s.specialization, cr.status
                FROM connection_requests cr
                JOIN users s ON cr.student_id = s.id
                WHERE cr.status = "Accepted"
                """)
    students = cursor.fetchall()
    conn.close()
    
    return render_template("connected_students.html", students=students)

@app.route("/student/<int:student_id>")
def view_student(student_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, specialization FROM users WHERE id = ?", (student_id,))
    
    student = cursor.fetchone()
    conn.close()
    
    if student is None:
        return f"Student not found"
    
    return render_template("student_profile.html", student=student, mentor=student)

@app.route("/student/<int:student_id>/performance")
def student_performance(student_id):
    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM users WHERE id =?", (student_id,))
    student = cursor.fetchone()
    conn.close()
    grades = {
        "Mathematics": 45,
        "Programming": 72,
        "Physics": 58,
        "Computer Network": 80
    }
    return render_template("student_performance.html", student=student, grades=grades)


@app.route("/view_mentor/<int:student_id>")
def view_mentor(student_id):
    import sqlite3
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    mentor = None
    mentor_performance = [] 
    pending_request = False
    c.execute("SELECT mentor_id FROM connection_requests WHERE student_id=? AND LOWER (status)='accepted' LIMIT 1",(student_id,))
    row = c.fetchone()
    
    if row:
        mentor_id = row[0]
        c.execute("SELECT * FROM users WHERE id =?", (mentor_id,))
        mentor = c.fetchone()
        c.execute("SELECT * FROM mentor_performance WHERE mentor_id =?", (mentor_id,))
        mentor_performance = c.fetchall()
    else:
        c.execute("SELECT * FROM connection_requests WHERE student_id=? AND LOWER(status)='pending' LIMIT 1", (student_id,))
        if c.fetchone():
            pending_request = True  
    conn.close()
    return render_template("view_mentor.html", student_id=student_id, mentor=mentor, mentor_performance = mentor_performance, pending_request = pending_request)

@app.route("/request_mentor/<int:mentor_id>", methods=["POST"])
def request_mentor(mentor_id):
    student_id = session.get("user_id")
    if not student_id:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
            SELECT id FROM connection_requests
            WHERE student_id = ? AND status = 'pending'
            """, (student_id,))
    if cursor.fetchone():
        conn.close()
        return "You already have a request pending"
    cursor.execute("""
            INSERT INTO connection_requests(student_id, mentor_id, status)
            VALUES (?,?, "pending)
            """, (student_id, mentor_id))
    conn.commit()
    conn.close()
    return redirect(f"/view_mentor/{student_id}")
    
@app.route("/mentor_performance/<int:mentor_id>")
def mentor_performance(mentor_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
            SLECT name, specialization
            FROM users
            WHERE id = ?
            """, (mentor_id, ))
    mentor = cursor.fetchone()
    conn.close()
    if mentor is None:
        return "Mentor not found"
    return render_template("mentor_performance.html", mentor=mentor)

@app.route("/request_mentor", methods=["GET", "POST"])
def request_mentor_simple():
    import sqlite3 
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO connection_requests (student_id, mentor_id, status) VALUES (2, 1, 'accepted')")
    conn.commit()
    conn.close()
    return redirect("/view_mentor/2")

@app.route("/mentor_dashboard")
def mentor_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
    mentor = cursor.fetchone()
    
    conn.close()
    return render_template("mentor_dashboard.html", mentor=mentor)
init_db()
create_test_users()
if __name__== "__main__":
    app.run(debug=True)