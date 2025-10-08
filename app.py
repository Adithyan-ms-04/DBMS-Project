from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project, Bid, FreelancerProfile, Milestone, Review
from config import Config
from datetime import datetime
from sqlalchemy import func

# ========================
# APP SETUP & CONFIG
# ========================

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
# AUTHENTICATION ROUTES
# ========================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.Role == 'freelancer':
            return redirect(url_for('freelancer_dashboard'))
        elif current_user.Role == 'client':
            return redirect(url_for('client_dashboard'))
        elif current_user.Role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(Email=email).first()
        
        if user and check_password_hash(user.Password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(Email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(Name=name, Email=email, Password=hashed_password, Role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'freelancer':
            freelancer_profile = FreelancerProfile(FreelancerID=new_user.UserID)
            db.session.add(freelancer_profile)
            db.session.commit()
            
        flash('Registration successful! Please log in.', 'success')
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
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    bids = Bid.query.filter_by(FreelancerID=current_user.UserID).all()
    open_projects = Project.query.filter_by(Status='open').all()
    return render_template('dashboard/freelancer.html', bids=bids, open_projects=open_projects)

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    if current_user.Role != 'client':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    projects = Project.query.filter_by(ClientID=current_user.UserID).all()
    return render_template('dashboard/client.html', projects=projects)

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if current_user.Role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    stats = {
        'total_users': User.query.count(),
        'total_projects': Project.query.count(),
        'total_bids': Bid.query.count()
    }
    recent_projects = Project.query.order_by(Project.CreatedAt.desc()).limit(5).all()
    return render_template('dashboard/admin.html', stats=stats, recent_projects=recent_projects)

# ========================
# PROJECT ROUTES
# ========================

@app.route('/projects')
@login_required
def view_projects():
    projects = Project.query.filter_by(Status='open').order_by(Project.CreatedAt.desc()).all()
    return render_template('projects/view_projects.html', projects=projects)

@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if current_user.Role != 'client':
        flash('Only clients can create projects.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        new_project = Project(
            ClientID=current_user.UserID,
            Title=request.form['title'],
            Description=request.form['description'],
            Budget=request.form['budget']
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
    bids = Bid.query.filter_by(ProjectID=project_id).order_by(Bid.BidDate.desc()).all()
    milestones = Milestone.query.filter_by(ProjectID=project_id).order_by(Milestone.DueDate).all()
    
    accepted_bid = Bid.query.filter_by(ProjectID=project_id, Status='accepted').first()
    assigned_freelancer = User.query.get(accepted_bid.FreelancerID) if accepted_bid else None

    return render_template('projects/project_details.html', 
                           project=project, 
                           bids=bids,
                           milestones=milestones,
                           assigned_freelancer=assigned_freelancer)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.ClientID != current_user.UserID:
        flash('Access denied.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    if request.method == 'POST':
        project.Title = request.form['title']
        project.Description = request.form['description']
        project.Budget = request.form['budget']
        project.Status = request.form['status']
        db.session.commit()
        flash('Project updated successfully.', 'success')
        return redirect(url_for('project_details', project_id=project_id))
        
    return render_template('projects/edit_project.html', project=project)

@app.route('/projects/<int:project_id>/close', methods=['POST'])
@login_required
def close_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.ClientID != current_user.UserID:
        flash('Access denied.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    project.Status = 'completed'
    db.session.commit()
    flash('Project has been marked as completed.', 'success')
    return redirect(url_for('project_details', project_id=project_id))

# ========================
# BID MANAGEMENT ROUTES
# ========================

@app.route('/projects/<int:project_id>/bid', methods=['POST'])
@login_required
def place_bid(project_id):
    if current_user.Role != 'freelancer':
        flash('Only freelancers can place bids.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    if Bid.query.filter_by(ProjectID=project_id, FreelancerID=current_user.UserID).first():
        flash('You have already placed a bid on this project.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
        
    new_bid = Bid(
        ProjectID=project_id,
        FreelancerID=current_user.UserID,
        BidAmount=request.form['bid_amount'],
        CoverLetter=request.form['cover_letter']
    )
    db.session.add(new_bid)
    db.session.commit()
    flash('Bid placed successfully.', 'success')
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/projects/<int:project_id>/accept_bid/<int:bid_id>', methods=['POST'])
@login_required
def accept_bid(project_id, bid_id):
    project = Project.query.get_or_404(project_id)
    bid = Bid.query.get_or_404(bid_id)
    
    if project.ClientID != current_user.UserID:
        flash('Access denied.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    project.Status = 'in_progress'
    bid.Status = 'accepted'
    Bid.query.filter_by(ProjectID=project_id).filter(Bid.BidID != bid_id).update({'Status': 'rejected'})
    db.session.commit()
    
    flash(f'Bid from {bid.freelancer.Name} accepted. Project is now in progress.', 'success')
    return redirect(url_for('project_details', project_id=project_id))
@app.route('/my_bids')
@login_required
def my_bids():
    # Ensure only freelancers can access this page
    if current_user.Role != 'freelancer':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Fetch all bids made by the current freelancer, ordered by the most recent
    bids = Bid.query.filter_by(FreelancerID=current_user.UserID).order_by(Bid.BidDate.desc()).all()
    
    # NOTE: You must create a 'my_bids.html' template in the 'templates/bids/' directory for this page to render.
    return render_template('bids/my_bids.html', bids=bids)

# ========================
# PROFILE ROUTES
# ========================

@app.route('/profile')
@login_required
def view_profile():
    user = current_user
    freelancer_profile = None
    reviews_received = []
    average_rating = 0
    
    if user.Role == 'freelancer':
        freelancer_profile = FreelancerProfile.query.filter_by(FreelancerID=user.UserID).first()
        avg_rating_query = db.session.query(func.avg(Review.Rating)).filter(Review.RevieweeID == user.UserID).scalar()
        average_rating = round(avg_rating_query, 2) if avg_rating_query else 0
        reviews_received = Review.query.filter_by(RevieweeID=user.UserID).order_by(Review.CreatedAt.desc()).all()
    
    return render_template('profile/view_profile.html', 
                           user=user, 
                           freelancer_profile=freelancer_profile,
                           reviews_received=reviews_received,
                           average_rating=average_rating)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    freelancer_profile = FreelancerProfile.query.filter_by(FreelancerID=user.UserID).first() if user.Role == 'freelancer' else None
    
    if request.method == 'POST':
        user.Name = request.form['name']
        user.Email = request.form['email']
        if user.Role == 'freelancer' and freelancer_profile:
            freelancer_profile.Skills = request.form['skills']
            freelancer_profile.Experience = request.form['experience']
            freelancer_profile.PortfolioURL = request.form['portfolio_url']
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('view_profile'))
    
    return render_template('profile/edit_profile.html', user=user, freelancer_profile=freelancer_profile)

# ========================
# MILESTONE & REVIEW ROUTES
# ========================

@app.route('/projects/<int:project_id>/milestones/create', methods=['POST'])
@login_required
def create_milestone(project_id):
    project = Project.query.get_or_404(project_id)
    if project.ClientID != current_user.UserID:
        flash('Access denied.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    new_milestone = Milestone(
        ProjectID=project_id,
        Title=request.form.get('title'),
        Description=request.form.get('description'),
        DueDate=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
        Amount=request.form.get('amount')
    )
    db.session.add(new_milestone)
    db.session.commit()
    flash('Milestone created successfully.', 'success')
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/milestones/<int:milestone_id>/complete', methods=['POST'])
@login_required
def complete_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    if current_user.UserID != milestone.project.ClientID:
        flash('Access denied.', 'error')
        return redirect(url_for('project_details', project_id=milestone.ProjectID))
    
    milestone.Status = 'completed'
    db.session.commit()
    flash('Milestone marked as complete.', 'success')
    return redirect(url_for('project_details', project_id=milestone.ProjectID))

@app.route('/projects/<int:project_id>/review', methods=['POST'])
@login_required
def submit_review(project_id):
    project = Project.query.get_or_404(project_id)
    if project.ClientID != current_user.UserID:
        flash('Only the client can review this project.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    if project.Status != 'completed':
        flash('You can only review completed projects.', 'error')
        return redirect(url_for('project_details', project_id=project_id))

    accepted_bid = Bid.query.filter_by(ProjectID=project_id, Status='accepted').first()
    if not accepted_bid:
        flash('Cannot find an assigned freelancer to review.', 'error')
        return redirect(url_for('project_details', project_id=project_id))
    
    reviewee_id = accepted_bid.FreelancerID
    if Review.query.filter_by(ProjectID=project_id, ReviewerID=current_user.UserID, RevieweeID=reviewee_id).first():
        flash('You have already submitted a review for this project.', 'error')
        return redirect(url_for('project_details', project_id=project_id))

    new_review = Review(
        ProjectID=project_id,
        ReviewerID=current_user.UserID,
        RevieweeID=reviewee_id,
        Rating=request.form.get('rating'),
        Comment=request.form.get('comment')
    )
    db.session.add(new_review)
    db.session.commit()
    flash('Thank you for your review!', 'success')
    return redirect(url_for('project_details', project_id=project_id))

# ========================
# ADMIN ROUTES
# ========================

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.Role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/projects')
@login_required
def admin_projects():
    if current_user.Role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    projects = Project.query.all()
    return render_template('admin/projects.html', projects=projects)

# ========================
# ERROR HANDLERS
# ========================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ========================
# APP START
# ========================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)