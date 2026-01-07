import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import text  # Required for the database fix

app = Flask(__name__)

# --- 1. CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yegosun-master-key-2026')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///yegosun.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CLOUDINARY CONFIG ---
cloudinary.config(
    cloud_name = 'dlwyo4bho', 
    api_key = '547698432919746', 
    api_secret = 'JcI3yNuHDxlAlXMbLG1uaXF3gYw' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- 2. DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # FIX: Increased size from 128 to 256 to fit the long hash
    password_hash = db.Column(db.String(256)) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(300), nullable=False) 
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- 3. PUBLIC ROUTES ---
@app.route('/')
def home():
    try:
        latest_blogs = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    except:
        latest_blogs = []
    return render_template('index.html', blogs=latest_blogs)

@app.route('/submit_quote', methods=['POST'])
def submit_quote():
    return redirect(url_for('home'))

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_detail.html', post=post)

# --- 4. ADMIN ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    all_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('dashboard.html', posts=all_posts)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        file = request.files['image']
        if file:
            try:
                res = cloudinary.uploader.upload(file)
                new_post = BlogPost(title=title, content=content, category=category, image_url=res['secure_url'])
                db.session.add(new_post)
                db.session.commit()
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(e)
    return render_template('create_post.html')

@app.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- 5. THE FIX ROUTE ---
@app.route('/setup-admin')
def setup_admin():
    try:
        # STEP A: Force the database to expand the column size
        # This prevents the "value too long" error
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(256);'))
            conn.commit()
            print("Database column resized successfully.")
    except Exception as e:
        print(f"Column resize warning (might already be done): {e}")

    try:
        # STEP B: Create/Reset the Admin User
        user = User.query.filter_by(username='admin').first()
        if user:
            user.set_password('password123')
            db.session.commit()
            return "SUCCESS: Existing 'admin' password reset to 'password123'. Database fixed."
        else:
            new_user = User(username='admin')
            new_user.set_password('password123')
            db.session.add(new_user)
            db.session.commit()
            return "SUCCESS: New 'admin' user created. Database fixed."
            
    except Exception as e:
        return f"Final Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)