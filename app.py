from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="fprms_user",
        password="fprms_pass",
        database="fprms"
    )

@app.route('/')
def home():
    return render_template('login.html')

# ---------------- Register ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', message=None)

    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if not all([name,email,password,role]):
        return render_template('register.html', message="All fields are required")

    hashed = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (Name,Email,Password,Role) VALUES (%s,%s,%s,%s)",
                       (name,email,hashed,role))
        conn.commit()
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        return render_template('register.html', message="Email already exists")
    cursor.close()
    conn.close()

    return render_template('login.html', message="Registered successfully! Please login.")

# ---------------- Login ----------------
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if not all([email,password,role]):
        return "All fields required", 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE Email=%s AND Role=%s",(email,role))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['Password'], password):
        session['user_id'] = user['UserID']
        session['role'] = user['Role']

        if user['Role'] == 'client':
            return redirect(url_for('client_dashboard_page'))
        elif user['Role'] == 'freelancer':
            return redirect(url_for('freelancer_dashboard_page'))
        elif user['Role'] == 'admin':
            return redirect(url_for('admin_dashboard_page'))
    return redirect(url_for('home', error="Invalid credentials"))

# ---------------- Dashboards ----------------
@app.route('/client_dashboard_page')
def client_dashboard_page():
    if session.get('role') != 'client':
        return redirect(url_for('home'))
    return render_template('client_dashboard.html')

@app.route('/freelancer_dashboard_page')
def freelancer_dashboard_page():
    if session.get('role') != 'freelancer':
        return redirect(url_for('home'))
    return render_template('freelancer_dashboard.html')

@app.route('/admin_dashboard_page')
def admin_dashboard_page():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
