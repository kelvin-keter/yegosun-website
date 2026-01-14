import os
import io
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from xhtml2pdf import pisa

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yegosun-master-key-2026')
basedir = os.path.abspath(os.path.dirname(__file__))

# *** FIXED DATABASE CONNECTION LOGIC ***
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # 1. Check if it's the old style (postgres://) and fix it
    if database_url.startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
    # 2. If it's already correct (postgresql://), use it directly
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"✅ CONNECTED TO EXTERNAL DATABASE") 
else:
    # 3. Fallback to local SQLite (Only happens if DATABASE_URL is missing)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'yegosun.db')
    print("⚠️ WARNING: USING TEMPORARY LOCAL DB")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL') 

mail = Mail(app)

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
    date_updated = db.Column(db.DateTime, nullable=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    system_size = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    impact = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='Completed')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    image_url = db.Column(db.String(300), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    project_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=True)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPER: SEND EMAIL ---
def send_admin_notification(subject, body):
    try:
        admin_email = app.config['ADMIN_EMAIL']
        if not admin_email or not app.config['MAIL_USERNAME']:
            print("Email config missing. Skipping notification.")
            return

        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[admin_email])
        msg.body = body
        mail.send(msg)
        print("Notification email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- ROUTES ---

@app.route('/db-upgrade')
def db_upgrade():
    try:
        db.create_all()
        return "SUCCESS: Database checked/updated."
    except Exception as e:
        return f"Error: {e}"

@app.route('/')
def home():
    try:
        latest_blogs = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
        featured_projects = Project.query.order_by(Project.date_posted.desc()).limit(3).all()
        testimonials = Testimonial.query.order_by(Testimonial.date_posted.desc()).limit(3).all()
    except:
        latest_blogs = []
        featured_projects = []
        testimonials = []
    return render_template('index.html', blogs=latest_blogs, projects=featured_projects, testimonials=testimonials)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    all_projects = Project.query.order_by(Project.date_posted.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit_quote', methods=['POST'])
def submit_quote():
    full_name = request.form.get('fullName')
    email = request.form.get('email')
    phone = request.form.get('phone')
    project_type = request.form.get('projectType')
    location = request.form.get('location')
    message = request.form.get('message')
    
    try:
        new_quote = Quote(full_name=full_name, email=email, phone=phone, project_type=project_type, location=location, message=message)
        db.session.add(new_quote)
        db.session.commit()
        
        email_body = f"""
        New Lead Received!
        ------------------
        Name: {full_name}
        Phone: {phone}
        Type: {project_type}
        Location: {location}
        Message: {message}
        
        Log in to dashboard to view details.
        """
        send_admin_notification(f"New Lead: {full_name}", email_body)
        
    except Exception as e:
        print(f"Error processing quote: {e}")
    
    rendered_html = render_template('pdf_quote.html', name=full_name, email=email, phone=phone, service=project_type, date=datetime.now().strftime("%Y-%m-%d"))
    pdf_file = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered_html), dest=pdf_file)
    pdf_file.seek(0)
    response = make_response(pdf_file.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Yegosun_Quote.pdf'
    return response

@app.route('/generate_report', methods=['POST'])
def generate_report():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    try: monthly_bill = float(request.form.get('monthly_bill'))
    except: monthly_bill = 0.0
    appliances = request.form.getlist('appliances')
    
    monthly_units = monthly_bill / 28
    daily_units = monthly_units / 30
    required_system_size = daily_units / 4.5 
    recommended_kw = round(required_system_size * 2) / 2
    if recommended_kw < 1: recommended_kw = 1
    est_cost_min = int(recommended_kw * 130000)
    est_cost_max = int(recommended_kw * 160000)
    monthly_savings = int(monthly_bill * 0.9)
    yearly_savings = monthly_savings * 12
    avg_cost = (est_cost_min + est_cost_max) / 2
    roi_years = round((avg_cost / monthly_savings)/12, 1) if monthly_savings > 0 else 0

    lead_details = f"Solar Report. Bill: {monthly_bill}. Sys: {recommended_kw}kW. Apps: {', '.join(appliances)}"
    
    try:
        new_lead = Quote(full_name=full_name, email=email, phone=phone, project_type="Solar Report", location="Web Calc", message=lead_details)
        db.session.add(new_lead)
        db.session.commit()
        
        email_body = f"""
        New Solar Calculator Lead!
        --------------------------
        Name: {full_name}
        Phone: {phone}
        Bill: KES {monthly_bill}
        Recommended System: {recommended_kw}kW
        Appliances: {', '.join(appliances)}
        """
        send_admin_notification(f"Calculator Lead: {full_name}", email_body)
    except: pass

    rendered_html = render_template('pdf_solar_report.html', name=full_name, date=datetime.now().strftime("%d %b %Y"), bill=monthly_bill, system_size=recommended_kw, cost_min="{:,}".format(est_cost_min), cost_max="{:,}".format(est_cost_max), savings="{:,}".format(yearly_savings), roi=roi_years, appliances=appliances)
    pdf_file = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered_html), dest=pdf_file)
    pdf_file.seek(0)
    response = make_response(pdf_file.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Solar_Report.pdf'
    return response

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_detail.html', post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            flash(f"Login error: {str(e)}", 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    all_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    all_quotes = Quote.query.order_by(Quote.date_submitted.desc()).all()
    all_projects = Project.query.order_by(Project.date_posted.desc()).all()
    testimonials = Testimonial.query.order_by(Testimonial.date_posted.desc()).all()
    return render_template('dashboard.html', posts=all_posts, quotes=all_quotes, projects=all_projects, testimonials=testimonials)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            category = request.form.get('category')
            file = request.files.get('image')
            image_url = ""
            if file and file.filename != '':
                res = cloudinary.uploader.upload(file)
                image_url = res['secure_url']
            new_post = BlogPost(title=title, content=content, category=category, image_url=image_url)
            db.session.add(new_post)
            db.session.commit()
            flash('Post created!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('create_post.html')

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == 'POST':
        try:
            post.title = request.form.get('title')
            post.content = request.form.get('content')
            post.category = request.form.get('category')
            post.date_updated = datetime.utcnow()
            file = request.files.get('image')
            if file and file.filename != '':
                res = cloudinary.uploader.upload(file)
                post.image_url = res['secure_url']
            db.session.commit()
            flash('Updated!', 'success')
            return redirect(url_for('dashboard'))
        except:
            flash('Error updating.', 'danger')
    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            system_size = request.form.get('system_size')
            location = request.form.get('location')
            description = request.form.get('description')
            impact = request.form.get('impact')
            status = request.form.get('status')
            file = request.files.get('image')
            
            image_url = ""
            if file and file.filename != '':
                res = cloudinary.uploader.upload(file)
                image_url = res['secure_url']
            
            project = Project(title=title, category=category, system_size=system_size, location=location, description=description, impact=impact, status=status, image_url=image_url)
            db.session.add(project)
            db.session.commit()
            flash('Project added!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('create_project.html')

@app.route('/project/<int:project_id>/delete')
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/testimonial/new', methods=['GET', 'POST'])
@login_required
def new_testimonial():
    if request.method == 'POST':
        try:
            client_name = request.form.get('client_name')
            role = request.form.get('role')
            content = request.form.get('content')
            rating = request.form.get('rating')
            file = request.files.get('image')
            image_url = ""
            if file and file.filename != '':
                res = cloudinary.uploader.upload(file)
                image_url = res['secure_url']
            testimonial = Testimonial(client_name=client_name, role=role, content=content, rating=rating, image_url=image_url)
            db.session.add(testimonial)
            db.session.commit()
            flash('Testimonial added!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('create_testimonial.html')

@app.route('/testimonial/<int:id>/delete')
@login_required
def delete_testimonial(id):
    t = Testimonial.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/quote/<int:quote_id>/delete')
@login_required
def delete_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    flash('Lead deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)