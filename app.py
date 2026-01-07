import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# --- 1. CONFIGURATION ---
app.config['SECRET_KEY'] = 'yegosun-master-key-2026' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yegosun.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CLOUDINARY CONFIG (Your Keys) ---
cloudinary.config(
    cloud_name = 'dlwyo4bho', 
    api_key = '547698432919746', 
    api_secret = 'JcI3yNuHDxlAlXMbLG1uaXF3gYw' 
)

# --- INIT EXTENSIONS ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- 2. DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # Stores the full Cloudinary URL (e.g., https://res.cloudinary.com/...)
    image_url = db.Column(db.String(300), nullable=False) 
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create Tables
with app.app_context():
    db.create_all()

# --- 3. PUBLIC ROUTES ---

@app.route('/')
def home():
    # Fetch 3 most recent blogs
    latest_blogs = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    return render_template('index.html', blogs=latest_blogs)

@app.route('/submit_quote', methods=['POST'])
def submit_quote():
    print(f"Quote received: {request.form.get('fullName')}")
    return redirect(url_for('home'))

# Placeholder for blog details
@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return f"<h1>{post.title}</h1><img src='{post.image_url}' width='500'><p>{post.content}</p>"

# --- 4. ADMIN DASHBOARD ROUTES ---

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
            flash('Invalid username or password')
            
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
        file_to_upload = request.files['image']

        if file_to_upload:
            try:
                # 1. Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(file_to_upload)
                # 2. Get the Secure URL
                image_url = upload_result['secure_url']
                
                # 3. Save to Database
                new_post = BlogPost(title=title, content=content, category=category, image_url=image_url)
                db.session.add(new_post)
                db.session.commit()
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error uploading: {e}")
                return "Error uploading image", 500

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

if __name__ == '__main__':
    app.run(debug=True)