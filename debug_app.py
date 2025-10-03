from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://fprms_user:fprms_pass@localhost/fprms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Simple User model for testing
class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.String(20), nullable=False)
    
    def get_id(self):
        return str(self.UserID)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(f"Login attempt: {email}")  # Debug print
        
        try:
            user = User.query.filter_by(Email=email).first()
            if user:
                print(f"User found: {user.Name}")  # Debug print
                if check_password_hash(user.Password, password):
                    login_user(user)
                    flash('Login successful!', 'success')
                    print("Login successful!")  # Debug print
                    
                    # Redirect based on role
                    if user.Role == 'freelancer':
                        return redirect(url_for('freelancer_dashboard'))
                    elif user.Role == 'client':
                        return redirect(url_for('client_dashboard'))
                    else:
                        return redirect(url_for('admin_dashboard'))
                else:
                    print("Password incorrect")  # Debug print
                    flash('Invalid password!', 'error')
            else:
                print("User not found")  # Debug print
                flash('User not found!', 'error')
                
        except Exception as e:
            print(f"Login error: {str(e)}")  # Debug print
            flash(f'Login error: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/dashboard/freelancer')
@login_required
def freelancer_dashboard():
    return "Freelancer Dashboard - Working!"

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    return "Client Dashboard - Working!"

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    return "Admin Dashboard - Working!"

@app.route('/test-db')
def test_db():
    try:
        users = User.query.all()
        return f"Database connected! Users: {len(users)}"
    except Exception as e:
        return f"Database error: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
            
            # Create a test user if none exists
            if not User.query.filter_by(Email='test@test.com').first():
                test_user = User(
                    Name='Test User',
                    Email='test@test.com',
                    Password=generate_password_hash('test123'),
                    Role='client'
                )
                db.session.add(test_user)
                db.session.commit()
                print("Test user created: test@test.com / test123")
                
        except Exception as e:
            print(f"Database setup error: {e}")
    
    app.run(debug=True, port=5000)