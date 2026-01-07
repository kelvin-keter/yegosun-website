from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'yegosun-secure-key-2026' # Change this for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yegosun.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # This will hold the filename (e.g., 'solar-school.jpg') located in static/images
    image_file = db.Column(db.String(50), nullable=False, default='hero-2.jpg') 
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

# Create Database tables (Run this once)
with app.app_context():
    db.create_all()
    
    # --- OPTIONAL: Create a Dummy Post if DB is empty (For testing) ---
    if not BlogPost.query.first():
        sample_post = BlogPost(
            title="Why Every Kenyan School Should Go Solar",
            content="Rising electricity costs are eating into school budgets. By switching to solar, institutions can save up to 60% on overheads...",
            category="Sustainability",
            image_file="hero-1.jpg" # Using one of your local hero images as a test
        )
        db.session.add(sample_post)
        db.session.commit()
        print("Created sample blog post!")

# --- ROUTES ---

@app.route('/')
def home():
    # Fetch the 3 most recent blogs
    latest_blogs = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    return render_template('index.html', blogs=latest_blogs)

@app.route('/submit_quote', methods=['POST'])
def submit_quote():
    # Here you would add logic to email the quote or save to DB
    print(f"Quote received: {request.form.get('fullName')}")
    return redirect(url_for('home'))

# Placeholder for future blog detail page
@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return f"<h1>{post.title}</h1><p>{post.content}</p>" # We will style this later

if __name__ == '__main__':
    app.run(debug=True)