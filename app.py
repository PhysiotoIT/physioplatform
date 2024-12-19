from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)

# Konfiguracja SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
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

# Tworzenie tabeli w bazie danych
with app.app_context():
    db.create_all()

# Funkcja do uwierzytelnienia
def check_auth(username, password):
    return username == 'admin' and password == 'secret'

# Funkcja zwracająca odpowiedź o braku dostępu
def authenticate():
    return Response(
        'Access denied. Please provide valid credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

# Dekorator do zabezpieczenia endpointu
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
    return "Welcome to the Physiotherapy Platform!"

# Endpoint do rejestracji pacjenta przez API
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

# Endpoint do rejestracji pacjenta przez formularz
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

# Endpoint do wyświetlania listy pacjentów (zabezpieczony hasłem)
@app.route('/patients', methods=['GET'])
@requires_auth
def list_patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)
