from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# Konfiguracja SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model pacjenta
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'

# Model posta blogowego
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False, default='Admin')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BlogPost {self.title}>'
    
# Model komentarzy
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False, default='Anonymous')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'

# Tworzenie tabel w bazie danych
with app.app_context():
    db.create_all()

# Funkcja do uwierzytelnienia
def check_auth(username, password):
    return username == 'admin' and password == 'secret'

def authenticate():
    return Response(
        'Access denied. Please provide valid credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Strona główna
@app.route('/')
def home():
    return render_template('index.html')

# Rejestracja pacjentów przez API
@app.route('/register', methods=['POST'])
def register_patient_api():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone')

    if not first_name or not last_name or not email:
        return jsonify({"error": "First name, last name, and email are required"}), 400

    new_patient = Patient(first_name=first_name, last_name=last_name, email=email, phone=phone)
    try:
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({"message": "Patient registered successfully!"}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Email already exists."}), 400

# Rejestracja pacjentów przez formularz
@app.route('/register-patient', methods=['GET', 'POST'])
def register_patient_form():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        if not first_name or not last_name or not email:
            return render_template('register.html', error="All fields except phone are required.")

        new_patient = Patient(first_name=first_name, last_name=last_name, email=email, phone=phone)
        try:
            db.session.add(new_patient)
            db.session.commit()
            return redirect(url_for('register_patient_form', success="Patient registered successfully!"))
        except Exception:
            db.session.rollback()
            return render_template('register.html', error="Email already exists.")
    return render_template('register.html')

# Lista pacjentów
@app.route('/patients', methods=['GET'])
@requires_auth
def list_patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

# Blog - lista postów
@app.route('/blog', methods=['GET'])
def blog():
    posts = BlogPost.query.order_by(BlogPost.date_created.desc()).all()
    return render_template('blog.html', posts=posts)

# Blog - szczegóły posta
@app.route('/blog/<int:post_id>', methods=['GET', 'POST'])
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        # Pobranie danych z formularza
        content = request.form.get('content')
        author = request.form.get('author', 'Anonymous')

        # Walidacja
        if not content:
            return render_template('blog_post.html', post=post, comments=post.comments, error="Treść komentarza jest wymagana.")

        # Dodanie komentarza do bazy danych
        new_comment = Comment(content=content, author=author, post_id=post.id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('blog_post', post_id=post.id))

    # Pobranie komentarzy do posta
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.date_created.desc()).all()
    return render_template('blog_post.html', post=post, comments=comments)


# Blog - tworzenie nowego posta
@app.route('/blog/new', methods=['GET', 'POST'])
@requires_auth
def new_blog_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = request.form.get('author', 'Admin')

        if not title or not content:
            return render_template('new_blog_post.html', error="Title and content are required.")

        new_post = BlogPost(title=title, content=content, author=author)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('blog'))

    return render_template('new_blog_post.html')




if __name__ == '__main__':
    app.run(debug=True)
