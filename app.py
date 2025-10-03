from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project, Bid, FreelancerProfile, Milestone, Review
from config import Config
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========================
# BASIC ROUTES
# ========================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    # Redirect to appropriate dashboard based on user role
    if current_user.Role == 'freelancer':
        return redirect(url_for('freelancer_dashboard'))
    elif current_user.Role == 'client':
        return redirect(url_for('client_dashboard'))
    elif current_user.Role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('login'))

# ========================
# AUTHENTICATION ROUTES
# ========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(Email=email).first()
        
        if user and check_password_hash(user.Password, password):
            login_user(user)
            flash('Login successful!', 'success')
            
            if user.Role == 'freelancer':
                return redirect(url_for('freelancer_dashboard'))
            elif user.Role == 'client':
                return redirect(url_for('client_dashboard'))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(Email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(Name=name, Email=email, Password=hashed_password, Role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'freelancer':
            freelancer_profile = FreelancerProfile(
                FreelancerID=new_user.UserID,
                Skills=request.form.get('skills', ''),
                Experience=request.form.get('experience', ''),
                PortfolioURL=request.form.get('portfolio_url', '')
            )
            db.session.add(freelancer_profile)
            db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ========================
# DASHBOARD ROUTES
# ========================

@app.route('/dashboard/freelancer')
@login_required
def freelancer_dashboard():
    if current_user.Role != 'freelancer':
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    bids = Bid.query.filter_by(FreelancerID=current_user.UserID).all()
    open_projects = Project.query.filter_by(Status='open').all()
    
    return render_template('dashboard/freelancer.html', 
                         bids=bids, 
                         open_projects=open_projects)

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    if current_user.Role != 'client':
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    projects = Project.query.filter_by(ClientID=current_user.UserID).all()
    
    return render_template('dashboard/client.html', projects=projects)

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if current_user.Role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    
    total_users = User.query.count()
    total_projects = Project.query.count()
    total_bids = Bid.query.count()
    
    return render_template('dashboard/admin.html',
                         total_users=total_users,
                         total_projects=total_projects,
                         total_bids=total_bids)

# ========================
# PROJECT ROUTES
# ========================

@app.route('/projects')
@login_required
def view_projects():
    projects = Project.query.filter_by(Status='open').all()
    return render_template('projects/view_projects.html', projects=projects)

@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if current_user.Role != 'client':
        flash('Only clients can create projects!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        budget = request.form['budget']
        
        new_project = Project(
            ClientID=current_user.UserID,
            Title=title,
            Description=description,
            Budget=budget
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('client_dashboard'))
    
    return render_template('projects/create_project.html')

@app.route('/projects/<int:project_id>')
@login_required
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    bids = Bid.query.filter_by(ProjectID=project_id).all()
    
    return render_template('projects/project_details.html', 
                         project=project, 
                         bids=bids)

# ========================
# BID ROUTES
# ========================

@app.route('/projects/<int:project_id>/bid', methods=['POST'])
@login_required
def place_bid(project_id):
    if current_user.Role != 'freelancer':
        flash('Only freelancers can place bids!', 'error')
        return redirect(url_for('home'))
    
    bid_amount = request.form['bid_amount']
    cover_letter = request.form['cover_letter']
    
    existing_bid = Bid.query.filter_by(
        ProjectID=project_id, 
        FreelancerID=current_user.UserID
    ).first()
    
    if existing_bid:
        flash('You have already placed a bid on this project!', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    new_bid = Bid(
        ProjectID=project_id,
        FreelancerID=current_user.UserID,
        BidAmount=bid_amount,
        CoverLetter=cover_letter
    )
    
    db.session.add(new_bid)
    db.session.commit()
    
    flash('Bid placed successfully!', 'success')
    return redirect(url_for('project_details', project_id=project_id))

# ========================
# PROFILE ROUTES
# ========================

@app.route('/profile')
@login_required
def view_profile():
    return render_template('profile/view_profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Handle profile update logic here
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('view_profile'))
    
    return render_template('profile/edit_profile.html')

# ========================
# ERROR HANDLERS
# ========================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# ========================
# APPLICATION START
# ========================

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("🚀 Starting Flask application...")
    app.run(debug=True, host='127.0.0.1', port=5000)