from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# -----------------------------
# Database connection
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="fprms_user",
        password="fprms_pass",
        database="fprms"
    )

# -----------------------------
# Serve Frontend Pages
# -----------------------------
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/client_dashboard_page')
def client_dashboard_page():
    return render_template('client_dashboard.html')

@app.route('/freelancer_dashboard_page')
def freelancer_dashboard_page():
    return render_template('freelancer_dashboard.html')

# -----------------------------
# Register API
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([name,email,password,role]):
        return jsonify({'error':'All fields required'}), 400

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
        return jsonify({'error':str(e)}), 400
    cursor.close()
    conn.close()
    return jsonify({'message':'Registered successfully'}), 201

# -----------------------------
# Login API
# -----------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([email,password,role]):
        return jsonify({'error':'All fields required'}),400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE Email=%s AND Role=%s",(email,role))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['Password'], password):
        del user['Password']
        return jsonify({'user':user})
    return jsonify({'error':'Invalid credentials'}),401

# -----------------------------
# List Users
# -----------------------------
@app.route('/users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT UserID,Name,Email,Role FROM Users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

# -----------------------------
# Projects
# -----------------------------
@app.route('/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Projects (ClientID,Title,Description,Budget) VALUES (%s,%s,%s,%s)",
                   (data['client_id'],data['title'],data['description'],data['budget']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message':'Project created'}),201

@app.route('/projects', methods=['GET'])
def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Projects WHERE Status='open'")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)

# -----------------------------
# Bids
# -----------------------------
@app.route('/bids', methods=['POST'])
def place_bid():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Bids (ProjectID,FreelancerID,BidAmount,CoverLetter) VALUES (%s,%s,%s,%s)",
                   (data['project_id'], data['freelancer_id'], data['bid_amount'], data['cover_letter']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message':'Bid placed'}),201

@app.route('/bids/<int:project_id>', methods=['GET'])
def get_bids(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Bids WHERE ProjectID=%s", (project_id,))
    bids = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(bids)

# -----------------------------
# Milestones
# -----------------------------
@app.route('/milestones', methods=['POST'])
def create_milestone():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Milestones (ProjectID,Title,Description,Status,DueDate) VALUES (%s,%s,%s,%s,%s)",
                   (data['project_id'],data.get('title'),data.get('description'),'pending',data.get('due_date')))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message':'Milestone created'}),201

@app.route('/milestones/<int:project_id>', methods=['GET'])
def get_milestones(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Milestones WHERE ProjectID=%s",(project_id,))
    milestones = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(milestones)

# -----------------------------
# Reviews
# -----------------------------
@app.route('/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Reviews (ReviewerID,RevieweeID,ProjectID,Rating,Comment) VALUES (%s,%s,%s,%s,%s)",
                   (data['reviewer_id'],data['reviewee_id'],data['project_id'],data['rating'],data.get('comment')))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message':'Review submitted'}),201

@app.route('/reviews/<int:project_id>', methods=['GET'])
def get_reviews(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Reviews WHERE ProjectID=%s",(project_id,))
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(reviews)

# -----------------------------
# Run Flask
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
