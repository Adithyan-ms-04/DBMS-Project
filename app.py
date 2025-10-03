from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysql_connector import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "fprms_secret_key_2024"

# Database config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'fprms_user'
app.config['MYSQL_PASSWORD'] = 'fprms_pass'
app.config['MYSQL_DATABASE'] = 'fprms'

mysql = MySQL(app)

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "danger")
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_db_connection():
    return mysql.connection

# -------------------------------
# AUTH ROUTES
# -------------------------------

@app.route('/')
def home():
    if 'user_id' in session:
        if session['role'] == 'client':
            return redirect(url_for('client_dashboard'))
        elif session['role'] == 'freelancer':
            return redirect(url_for('freelancer_dashboard'))
        elif session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE Email=%s AND Role=%s", (email, role))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['Password'], password):
            session['user_id'] = user['UserID']
            session['role'] = user['Role']
            session['name'] = user['Name']
            flash(f"Welcome back, {user['Name']}!", "success")
            
            if user['Role'] == 'client':
                return redirect(url_for('client_dashboard'))
            elif user['Role'] == 'freelancer':
                return redirect(url_for('freelancer_dashboard'))
            elif user['Role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email, password, or role selection", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, role)
            )
            mysql.connection.commit()
            
            if role == 'freelancer':
                user_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO Freelancer_Profile (FreelancerID, Title, Skills) VALUES (%s, %s, %s)",
                    (user_id, "New Freelancer", "Add your skills")
                )
                mysql.connection.commit()
            
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash("Email already exists or registration failed", "danger")
        finally:
            cursor.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# -------------------------------
# CLIENT ROUTES
# -------------------------------

@app.route('/client/dashboard')
@login_required(role='client')
def client_dashboard():
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get client's projects
    cursor.execute("""
        SELECT p.*, COUNT(b.BidID) as bid_count 
        FROM Projects p 
        LEFT JOIN Bids b ON p.ProjectID = b.ProjectID 
        WHERE p.ClientID = %s 
        GROUP BY p.ProjectID 
        ORDER BY p.CreatedAt DESC
    """, (session['user_id'],))
    projects = cursor.fetchall()
    
    # Get awarded projects in progress
    cursor.execute("""
        SELECT p.*, u.Name as freelancer_name 
        FROM Projects p 
        JOIN Project_Awards pa ON p.ProjectID = pa.ProjectID 
        JOIN Users u ON pa.FreelancerID = u.UserID 
        WHERE p.ClientID = %s AND p.Status = 'in_progress'
    """, (session['user_id'],))
    active_projects = cursor.fetchall()
    
    cursor.close()
    return render_template('client_dashboard.html', projects=projects, active_projects=active_projects)

@app.route('/client/new_project', methods=['GET', 'POST'])
@login_required(role='client')
def new_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        budget = request.form['budget']
        deadline = request.form['deadline']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO Projects (ClientID, Title, Description, Budget, Deadline, Status) 
            VALUES (%s, %s, %s, %s, %s, 'open')
        """, (session['user_id'], title, description, budget, deadline))
        mysql.connection.commit()
        cursor.close()
        
        flash("Project posted successfully!", "success")
        return redirect(url_for('client_dashboard'))

    return render_template('new_project.html')

@app.route('/client/project/<int:project_id>')
@login_required(role='client')
def client_project_detail(project_id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get project details
    cursor.execute("SELECT * FROM Projects WHERE ProjectID = %s AND ClientID = %s", (project_id, session['user_id']))
    project = cursor.fetchone()
    
    if not project:
        flash("Project not found", "danger")
        return redirect(url_for('client_dashboard'))
    
    # Get bids for this project
    cursor.execute("""
        SELECT b.*, u.Name as freelancer_name, u.Email, fp.Title as freelancer_title, fp.Skills
        FROM Bids b 
        JOIN Users u ON b.FreelancerID = u.UserID 
        LEFT JOIN Freelancer_Profile fp ON u.UserID = fp.FreelancerID 
        WHERE b.ProjectID = %s 
        ORDER BY b.BidAmount ASC
    """, (project_id,))
    bids = cursor.fetchall()
    
    # Check if project is awarded
    cursor.execute("""
        SELECT pa.*, u.Name as freelancer_name 
        FROM Project_Awards pa 
        JOIN Users u ON pa.FreelancerID = u.UserID 
        WHERE pa.ProjectID = %s
    """, (project_id,))
    award = cursor.fetchone()
    
    # Get milestones if project is awarded
    milestones = []
    if award:
        cursor.execute("SELECT * FROM Milestones WHERE ProjectID = %s ORDER BY DueDate", (project_id,))
        milestones = cursor.fetchall()
    
    cursor.close()
    return render_template('client_project_detail.html', project=project, bids=bids, award=award, milestones=milestones)

@app.route('/client/project/<int:project_id>/award/<int:freelancer_id>', methods=['POST'])
@login_required(role='client')
def award_project(project_id, freelancer_id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    try:
        # Get the bid ID
        cursor.execute("SELECT BidID FROM Bids WHERE ProjectID = %s AND FreelancerID = %s", (project_id, freelancer_id))
        bid = cursor.fetchone()
        
        if not bid:
            flash("Bid not found", "danger")
            return redirect(url_for('client_project_detail', project_id=project_id))
        
        # Award the project
        cursor.execute("""
            INSERT INTO Project_Awards (ProjectID, FreelancerID, BidID) 
            VALUES (%s, %s, %s)
        """, (project_id, freelancer_id, bid['BidID']))
        
        # Update project status
        cursor.execute("UPDATE Projects SET Status = 'in_progress' WHERE ProjectID = %s", (project_id,))
        
        # Reject all other bids
        cursor.execute("UPDATE Bids SET Status = 'rejected' WHERE ProjectID = %s AND FreelancerID != %s", (project_id, freelancer_id))
        
        # Accept the winning bid
        cursor.execute("UPDATE Bids SET Status = 'accepted' WHERE ProjectID = %s AND FreelancerID = %s", (project_id, freelancer_id))
        
        mysql.connection.commit()
        flash("Project awarded successfully!", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash("Error awarding project", "danger")
    finally:
        cursor.close()
    
    return redirect(url_for('client_project_detail', project_id=project_id))

@app.route('/client/project/<int:project_id>/milestones', methods=['POST'])
@login_required(role='client')
def create_milestone(project_id):
    title = request.form['title']
    description = request.form['description']
    amount = request.form['amount']
    due_date = request.form['due_date']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO Milestones (ProjectID, Title, Description, Amount, DueDate) 
            VALUES (%s, %s, %s, %s, %s)
        """, (project_id, title, description, amount, due_date))
        mysql.connection.commit()
        flash("Milestone created successfully!", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash("Error creating milestone", "danger")
    finally:
        cursor.close()
    
    return redirect(url_for('client_project_detail', project_id=project_id))

@app.route('/client/milestone/<int:milestone_id>/update_status', methods=['POST'])
@login_required(role='client')
def update_milestone_status(milestone_id):
    status = request.form['status']
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("UPDATE Milestones SET Status = %s WHERE MilestoneID = %s", (status, milestone_id))
        mysql.connection.commit()
        flash("Milestone status updated!", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash("Error updating milestone", "danger")
    finally:
        cursor.close()
    
    # Get project ID for redirect
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT ProjectID FROM Milestones WHERE MilestoneID = %s", (milestone_id,))
    milestone = cursor.fetchone()
    cursor.close()
    
    return redirect(url_for('client_project_detail', project_id=milestone['ProjectID']))

# -------------------------------
# FREELANCER ROUTES
# -------------------------------

@app.route('/freelancer/dashboard')
@login_required(role='freelancer')
def freelancer_dashboard():
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get available projects
    cursor.execute("""
        SELECT p.*, u.Name as client_name 
        FROM Projects p 
        JOIN Users u ON p.ClientID = u.UserID 
        WHERE p.Status = 'open' 
        ORDER BY p.CreatedAt DESC
    """)
    available_projects = cursor.fetchall()
    
    # Get freelancer's bids
    cursor.execute("""
        SELECT b.*, p.Title as project_title, p.Budget, p.Status as project_status 
        FROM Bids b 
        JOIN Projects p ON b.ProjectID = p.ProjectID 
        WHERE b.FreelancerID = %s 
        ORDER BY b.BidDate DESC
    """, (session['user_id'],))
    my_bids = cursor.fetchall()
    
    # Get awarded projects
    cursor.execute("""
        SELECT p.*, pa.AwardedAt, u.Name as client_name 
        FROM Projects p 
        JOIN Project_Awards pa ON p.ProjectID = pa.ProjectID 
        JOIN Users u ON p.ClientID = u.UserID 
        WHERE pa.FreelancerID = %s AND p.Status = 'in_progress'
    """, (session['user_id'],))
    awarded_projects = cursor.fetchall()
    
    cursor.close()
    return render_template('freelancer_dashboard.html', 
                         available_projects=available_projects, 
                         my_bids=my_bids, 
                         awarded_projects=awarded_projects)

@app.route('/freelancer/project/<int:project_id>')
@login_required(role='freelancer')
def freelancer_project_detail(project_id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get project details
    cursor.execute("""
        SELECT p.*, u.Name as client_name 
        FROM Projects p 
        JOIN Users u ON p.ClientID = u.UserID 
        WHERE p.ProjectID = %s
    """, (project_id,))
    project = cursor.fetchone()
    
    # Check if already bid
    cursor.execute("SELECT * FROM Bids WHERE ProjectID = %s AND FreelancerID = %s", (project_id, session['user_id']))
    existing_bid = cursor.fetchone()
    
    cursor.close()
    return render_template('freelancer_project_detail.html', project=project, existing_bid=existing_bid)

@app.route('/freelancer/project/<int:project_id>/bid', methods=['GET', 'POST'])
@login_required(role='freelancer')
def place_bid(project_id):
    if request.method == 'POST':
        bid_amount = request.form['bid_amount']
        cover_letter = request.form['cover_letter']
        estimated_days = request.form['estimated_days']

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO Bids (ProjectID, FreelancerID, BidAmount, CoverLetter, EstimatedDays) 
                VALUES (%s, %s, %s, %s, %s)
            """, (project_id, session['user_id'], bid_amount, cover_letter, estimated_days))
            mysql.connection.commit()
            flash("Bid placed successfully!", "success")
            return redirect(url_for('freelancer_dashboard'))
        except Exception as e:
            mysql.connection.rollback()
            flash("Error placing bid. You may have already bid on this project.", "danger")
        finally:
            cursor.close()

    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Projects WHERE ProjectID = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    
    return render_template('bid_form.html', project=project)

@app.route('/freelancer/awarded_projects')
@login_required(role='freelancer')
def awarded_projects():
    cursor = mysql.connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, pa.AwardedAt, u.Name as client_name 
        FROM Projects p 
        JOIN Project_Awards pa ON p.ProjectID = pa.ProjectID 
        JOIN Users u ON p.ClientID = u.UserID 
        WHERE pa.FreelancerID = %s
        ORDER BY pa.AwardedAt DESC
    """, (session['user_id'],))
    projects = cursor.fetchall()
    
    # Get milestones for these projects
    for project in projects:
        cursor.execute("""
            SELECT * FROM Milestones 
            WHERE ProjectID = %s 
            ORDER BY DueDate
        """, (project['ProjectID'],))
        project['milestones'] = cursor.fetchall()
    
    cursor.close()
    return render_template('awarded_projects.html', projects=projects)

@app.route('/freelancer/milestone/<int:milestone_id>/submit', methods=['POST'])
@login_required(role='freelancer')
def submit_milestone(milestone_id):
    cursor = mysql.connection.cursor(dictionary=True)
    
    try:
        # Verify the milestone belongs to a project awarded to this freelancer
        cursor.execute("""
            SELECT m.ProjectID 
            FROM Milestones m 
            JOIN Project_Awards pa ON m.ProjectID = pa.ProjectID 
            WHERE m.MilestoneID = %s AND pa.FreelancerID = %s
        """, (milestone_id, session['user_id']))
        
        milestone = cursor.fetchone()
        
        if not milestone:
            flash("Milestone not found or access denied", "danger")
            return redirect(url_for('awarded_projects'))
        
        cursor.execute("""
            UPDATE Milestones 
            SET Status = 'submitted', SubmittedAt = NOW() 
            WHERE MilestoneID = %s
        """, (milestone_id,))
        mysql.connection.commit()
        flash("Milestone submitted for review!", "success")
        
    except Exception as e:
        mysql.connection.rollback()
        flash("Error submitting milestone", "danger")
    finally:
        cursor.close()
    
    return redirect(url_for('awarded_projects'))

@app.route('/freelancer/profile', methods=['GET', 'POST'])
@login_required(role='freelancer')
def freelancer_profile():
    cursor = mysql.connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form['title']
        bio = request.form['bio']
        skills = request.form['skills']
        experience = request.form['experience']
        hourly_rate = request.form['hourly_rate']
        portfolio_url = request.form['portfolio_url']
        location = request.form['location']

        try:
            cursor.execute("""
                INSERT INTO Freelancer_Profile 
                (FreelancerID, Title, Bio, Skills, Experience, HourlyRate, PortfolioURL, Location) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                Title=%s, Bio=%s, Skills=%s, Experience=%s, HourlyRate=%s, PortfolioURL=%s, Location=%s
            """, (
                session['user_id'], title, bio, skills, experience, hourly_rate, portfolio_url, location,
                title, bio, skills, experience, hourly_rate, portfolio_url, location
            ))
            mysql.connection.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash("Error updating profile", "danger")
    
    # Get current profile
    cursor.execute("SELECT * FROM Freelancer_Profile WHERE FreelancerID = %s", (session['user_id'],))
    profile = cursor.fetchone()
    
    cursor.close()
    return render_template('freelancer_profile.html', profile=profile)

# -------------------------------
# ADMIN ROUTES
# -------------------------------

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total FROM Users")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Projects")
    total_projects = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Bids")
    total_bids = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Projects WHERE Status = 'open'")
    open_projects = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Projects WHERE Status = 'in_progress'")
    active_projects = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM Projects WHERE Status = 'completed'")
    completed_projects = cursor.fetchone()['total']
    
    # Get recent activities
    cursor.execute("""
        (SELECT 'project' as type, ProjectID as id, Title as name, CreatedAt as date FROM Projects ORDER BY CreatedAt DESC LIMIT 5)
        UNION ALL
        (SELECT 'bid' as type, BidID as id, CONCAT('Bid for Project #', ProjectID) as name, BidDate as date FROM Bids ORDER BY BidDate DESC LIMIT 5)
        ORDER BY date DESC LIMIT 10
    """)
    recent_activities = cursor.fetchall()
    
    cursor.close()
    
    stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_bids': total_bids,
        'open_projects': open_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects
    }
    
    return render_template('admin_dashboard.html', stats=stats, recent_activities=recent_activities)

@app.route('/admin/users')
@login_required(role='admin')
def admin_users():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users ORDER BY CreatedAt DESC")
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/projects')
@login_required(role='admin')
def admin_projects():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.Name as client_name 
        FROM Projects p 
        JOIN Users u ON p.ClientID = u.UserID 
        ORDER BY p.CreatedAt DESC
    """)
    projects = cursor.fetchall()
    cursor.close()
    return render_template('admin_projects.html', projects=projects)

# -------------------------------
# COMMON ROUTES
# -------------------------------

@app.route('/messages')
@login_required()
def messages():
    cursor = mysql.connection.cursor(dictionary=True)
    
    # Get conversations
    cursor.execute("""
        SELECT DISTINCT 
            CASE 
                WHEN SenderID = %s THEN ReceiverID 
                ELSE SenderID 
            END as other_user_id,
            u.Name as other_user_name,
            u.Role as other_user_role,
            MAX(SentAt) as last_message_date
        FROM Messages m
        JOIN Users u ON (CASE WHEN m.SenderID = %s THEN m.ReceiverID ELSE m.SenderID END) = u.UserID
        WHERE SenderID = %s OR ReceiverID = %s
        GROUP BY other_user_id
        ORDER BY last_message_date DESC
    """, (session['user_id'], session['user_id'], session['user_id'], session['user_id']))
    
    conversations = cursor.fetchall()
    
    # Get messages for selected conversation
    other_user_id = request.args.get('user_id')
    messages = []
    if other_user_id:
        cursor.execute("""
            SELECT m.*, u1.Name as sender_name, u2.Name as receiver_name
            FROM Messages m
            JOIN Users u1 ON m.SenderID = u1.UserID
            JOIN Users u2 ON m.ReceiverID = u2.UserID
            WHERE (m.SenderID = %s AND m.ReceiverID = %s) OR (m.SenderID = %s AND m.ReceiverID = %s)
            ORDER BY m.SentAt ASC
        """, (session['user_id'], other_user_id, other_user_id, session['user_id']))
        messages = cursor.fetchall()
    
    cursor.close()
    return render_template('messages.html', conversations=conversations, messages=messages, other_user_id=other_user_id)

@app.route('/send_message', methods=['POST'])
@login_required()
def send_message():
    receiver_id = request.form['receiver_id']
    message_text = request.form['message']
    project_id = request.form.get('project_id')

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO Messages (SenderID, ReceiverID, ProjectID, Message) 
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], receiver_id, project_id, message_text))
        mysql.connection.commit()
        flash("Message sent!", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash("Error sending message", "danger")
    finally:
        cursor.close()
    
    return redirect(url_for('messages', user_id=receiver_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    cursor = mysql.connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        try:
            cursor.execute("""
                UPDATE Users 
                SET Name = %s, Email = %s, Phone = %s 
                WHERE UserID = %s
            """, (name, email, phone, session['user_id']))
            mysql.connection.commit()
            session['name'] = name
            flash("Profile updated successfully!", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash("Error updating profile", "danger")
    
    cursor.execute("SELECT * FROM Users WHERE UserID = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    
    return render_template('profile.html', user=user)

# -------------------------------
# API ROUTES (for AJAX calls)
# -------------------------------

@app.route('/api/projects/search')
def search_projects():
    query = request.args.get('q', '')
    cursor = mysql.connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, u.Name as client_name 
        FROM Projects p 
        JOIN Users u ON p.ClientID = u.UserID 
        WHERE p.Status = 'open' AND (p.Title LIKE %s OR p.Description LIKE %s)
        ORDER BY p.CreatedAt DESC
    """, (f'%{query}%', f'%{query}%'))
    
    projects = cursor.fetchall()
    cursor.close()
    return jsonify(projects)

@app.route('/api/freelancers/search')
def search_freelancers():
    query = request.args.get('q', '')
    cursor = mysql.connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT u.UserID, u.Name, u.Email, fp.Title, fp.Skills, fp.Experience, fp.HourlyRate
        FROM Users u 
        JOIN Freelancer_Profile fp ON u.UserID = fp.FreelancerID 
        WHERE u.Role = 'freelancer' AND (u.Name LIKE %s OR fp.Skills LIKE %s OR fp.Title LIKE %s)
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    freelancers = cursor.fetchall()
    cursor.close()
    return jsonify(freelancers)

# -------------------------------
# ERROR HANDLERS
# -------------------------------

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    mysql.connection.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

# -------------------------------
# MAIN APPLICATION
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)