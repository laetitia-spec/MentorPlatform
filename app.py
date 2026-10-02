from flask import Flask, render_template, request
import sqlite3
app = Flask(__name__)

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
    
    if "specialization" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN specialization TEXT")
    conn.commit()
    conn.close()
init_db()

def create_test_users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    users = [
        ("Student One", "student@example.com", "1234", "student"),
        ("Math Mentor", "math@example.com", "1234", "mentor"),
        ("Programming Mentor", "programming@example.com", "1234", "mentor"),
        ("Physics Mentor", "physics@example.com", "1234", "mentor")
    ]
    for user in users:
        cursor.execute("""
            INSERT OR IGNORE INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, user)
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

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]
    
    return render_template("dashboard.html")
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
    return render_template("performance.html", grades=grades) 

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
        
        student_id = 1
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
            """, (student_id, mentor_id, "Pending"))
        
        conn.commit()
        conn.close()
        
        return "Connection request sent!"
    mentor_id = request.args.get("mentor_id")
    
    return render_template("connect.html", mentor_id=mentor_id)

@app.route("/requests")
def requests():
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
    return render_template("my_requests.html")

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
    
    return render_template("student_profile.html", student=student)

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

@app.route("/view_mentor")
@app.route("/view_mentor/<int:student_id>")
def view_mentor(student_id=None):
    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    mentor = None
    pending_request = None
    if student_id:
        cursor.execute("""
            SELECT users.id, users.name, users.email
            FROM connections
            JOIN users ON connections.mentor_id = users.id
            WHERE connections.student_id =?
            """, (student_id,))
    mentor = cursor.fetchone()
    if not mentor:
        cursor.execute("""
            SELECT id, mentor_id
            FROM mentor_requests
            WHERE student_id =? AND status = "pending"
            """, (student_id,))
        pending_request = cursor.fetchone()
    conn.close()
    return render_template("view_mentor.html", mentor=mentor, pending_request=pending_request, student_id=student_id)

if __name__== "__main__":
    app.run(debug=True)