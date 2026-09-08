from flask import Flask, render_template, request
app = Flask(__name__)

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
    return render_template("performance.html") 

@app.route("/courses")
def courses():
    return render_template("courses.html") 

@app.route("/mentorship")
def mentorship():
    return render_template("mentorship.html") 

@app.route("/recommendations")
def recommendations():
    return render_template("recommendations.html") 

if __name__=="__main__":
    app.run(debug=True)