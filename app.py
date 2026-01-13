import os
import io
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from xhtml2pdf import pisa

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yegosun-master-key-2026')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///yegosun.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CLOUDINARY ---
cloudinary.config(
    cloud_name = 'dlwyo4bho', 
    api_key = '547698432919746', 
    api_secret = 'JcI3yNuHDxlAlXMbLG1uaXF3gYw' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
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

# NEW MODEL: To track Quotes/Leads
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    project_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True) # New field
    message = db.Column(db.Text, nullable=True)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def home():
    try:
        latest_blogs = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    except:
        latest_blogs = []
    return render_template('index.html', blogs=latest_blogs)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# --- SUBMIT QUOTE (Save to DB + Generate PDF) ---
@app.route('/submit_quote', methods=['POST'])
def submit_quote():
    # 1. Get Data
    full_name = request.form.get('fullName')
    email = request.form.get('email')
    phone = request.form.get('phone')
    project_type = request.form.get('projectType')
    location = request.form.get('location') # New field
    message = request.form.get('message')

    # 2. SAVE TO DATABASE (The "Lead Capture" Step)
    try:
        new_quote = Quote(
            full_name=full_name,
            email=email,
            phone=phone,
            project_type=project_type,
            location=location,
            message=message
        )
        db.session.add(new_quote)
        db.session.commit()
    except Exception as e:
        print(f"Error saving quote: {e}")

    # 3. Render HTML for PDF
    rendered_html = render_template('pdf_quote.html', 
                                  name=full_name, 
                                  email=email, 
                                  phone=phone,
                                  service=project_type,
                                  date=datetime.now().strftime("%Y-%m-%d"))
    
    # 4. Create PDF in Memory
    pdf_file = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(rendered_html), dest=pdf_file)
    
    if pisa_status.err:
        return 'We had some errors creating the PDF', 500
    
    # 5. Return PDF
    pdf_file.seek(0)
    response = make_response(pdf_file.read())
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"Yegosun_Quote_{full_name.replace(' ', '_')}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_detail.html', post=post)

# --- ADMIN DASHBOARD ---

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
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch Blogs
    all_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    # Fetch Quotes (New!)
    all_quotes = Quote.query.order_by(Quote.date_submitted.desc()).all()
    
    return render_template('dashboard.html', posts=all_posts, quotes=all_quotes)

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

# New Route to delete a quote if needed
@app.route('/quote/<int:quote_id>/delete')
@login_required
def delete_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- TEMPORARY SETUP ROUTE ---
@app.route('/create_admin')
def create_admin():
    # 1. Check if admin exists
    existing_user = User.query.filter_by(username='admin').first()
    if existing_user:
        return "Admin user already exists! Go to /login"
    
    # 2. Create new admin
    new_user = User(username='admin')
    new_user.set_password('admin2026') # <--- YOUR PASSWORD
    db.session.add(new_user)
    db.session.commit()
    return "SUCCESS: Admin user created. You can now go to /login"

if __name__ == '__main__':
    app.run(debug=True)