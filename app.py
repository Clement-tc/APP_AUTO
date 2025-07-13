import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy import create_engine
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import fitz
from datetime import datetime
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", "uploads")
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

print("✅ DEBUG: SECRET_KEY from ENV =", os.getenv("SECRET_KEY"))
print("✅ DEBUG: Flask app.secret_key =", app.secret_key)

# (Déjà dans ton code actuel)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application Offre API', version='1.0.0')

db = SQLAlchemy(app)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class OffreEmploi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    localisation = db.Column(db.String(100), nullable=False)
    competences = db.Column(db.String(200), nullable=False)
    date_publication = db.Column(db.String(50), nullable=False)
    questions = db.Column(JSON, nullable=True)

class Candidat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cv = db.Column(db.String(3000), nullable=False)
    offre_id = db.Column(db.Integer, db.ForeignKey('offre_emploi.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    offre = db.relationship('OffreEmploi', backref=db.backref('candidats', lazy=True))
    user = db.relationship('User', backref=db.backref('candidatures', lazy=True))
    date_postulation = db.Column(db.String(50), nullable=False)
    reponses = db.Column(JSON, nullable=True)

def get_cv_text(df):
    return str(df['skills']) + " " + str(df['career_objective'])

with app.app_context():
    db.create_all()
    if OffreEmploi.query.count() == 0:
        offres = [
            OffreEmploi(titre="Analytics Engineer", description="Notre équipe Data recherche son / sa futur(e) stagiaire sur une fonction d’Analytics Engineer...", localisation="Paris", competences="Airflow, AWS, Python", date_publication="2025-05-01"),
            OffreEmploi(titre="Data Analyst", description="Analyser et visualiser les données...", localisation="Lyon", competences="SQL, Tableau, Python", date_publication="2025-05-02"),
            OffreEmploi(titre="Data Engineer", description="Construire des pipelines de données...", localisation="Marseille", competences="Python, SQL", date_publication="2025-05-03"),
            OffreEmploi(titre="Machine Learning Engineer", description="Développer des modèles ML...", localisation="Bordeaux", competences="TensorFlow, Kubernetes", date_publication="2025-05-04")
        ]
        db.session.add_all(offres)
        db.session.commit()

        df = pd.read_csv('resume_data.csv')
        for offre in offres:
            if Candidat.query.filter_by(offre_id=offre.id).count() == 0:
                for _, row in df.sample(n=np.random.randint(5, 11)).iterrows():
                    cv_text = get_cv_text(row)
                    user = User(username=f"user_{_}_{offre.id}", password="demo", role="candidat")
                    db.session.add(user)
                    db.session.commit()
                    candidat = Candidat(cv=cv_text, offre_id=offre.id, user_id=user.id, date_postulation=offre.date_publication)
                    db.session.add(candidat)
                    db.session.commit()

@app.route("/")
def home():
    offres = OffreEmploi.query.all()
    image_folder = os.path.join(app.static_folder, 'images')
    image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
    return render_template("home.html", offres=offres, image_files=image_files)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if not username or not password or not role:
            return render_template("signup.html", error="Tous les champs sont obligatoires.")
        if User.query.filter_by(username=username).first():
            return render_template("signup.html", error="Nom d'utilisateur déjà pris.")
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    return render_template("signup.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_offre():
    if current_user.role != 'recruteur':
        return redirect(url_for('home'))
    if request.method == "POST":
        questions = request.form.getlist('questions[]')
        offre = OffreEmploi(
            titre=request.form['titre'],
            description=request.form['description'],
            localisation=request.form['localisation'],
            competences=request.form['competences'],
            date_publication=datetime.today().strftime('%Y-%m-%d'),
            questions=[q for q in questions if q.strip()]
        )
        db.session.add(offre)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("create_offre.html")

@app.route("/postuler/<int:offre_id>", methods=["GET", "POST"])
@login_required
def postuler(offre_id):
    if current_user.role != 'candidat':
        return redirect(url_for('home'))
    offre = OffreEmploi.query.get_or_404(offre_id)
    if request.method == "POST":
        cv_file = request.files['cv']
        path = os.path.join(app.config['UPLOAD_FOLDER'], cv_file.filename)
        cv_file.save(path)
        cv_text = extract_text_from_pdf(path)
        reponses = request.form.getlist('reponses[]') if 'reponses[]' in request.form else []
        candidat = Candidat(cv=cv_text, offre_id=offre_id, user_id=current_user.id, date_postulation=datetime.today().strftime('%Y-%m-%d'), reponses=reponses)
        db.session.add(candidat)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("postuler.html", offre=offre)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return " ".join(page.get_text() for page in doc)

@app.route("/offre/<int:offre_id>")
def view_offre(offre_id):
    offre = OffreEmploi.query.get_or_404(offre_id)
    return render_template("view_offre.html", offre=offre)

@app.route("/mes-candidatures")
@login_required
def mes_candidatures():
    if current_user.role != "candidat":
        return redirect(url_for("home"))
    candidatures = Candidat.query.filter_by(user_id=current_user.id).all()
    return render_template("mes_candidatures.html", candidatures=candidatures)

@app.route("/analyze/<int:offre_id>")
@login_required
def analyze(offre_id):
    if current_user.role != 'recruteur':
        return redirect(url_for('home'))
    offre = OffreEmploi.query.get_or_404(offre_id)
    candidats = Candidat.query.filter_by(offre_id=offre_id).all()
    resultats = []
    for c in candidats:
        score = np.random.uniform(0,1)
        resultats.append((c.id, float(score)))
    resultats.sort(key=lambda x: x[1], reverse=True)
    moyenne_score = sum(x[1] for x in resultats) / len(resultats) if resultats else 0
    fig, ax = plt.subplots()
    ax.plot(range(len(resultats)), [x[1] for x in resultats], marker='o', linestyle='-', color='b')
    ax.set_title('Graphique des scores de similarité')
    ax.set_xlabel('Candidats (ID)')
    ax.set_ylabel('Score de Similarité')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    candidats_dict = {c.id: c for c in candidats}
    return render_template("analyze.html", offre=offre, table=resultats, moyenne_score=moyenne_score,
                           n_candidatures=len(resultats), img_base64=img_base64, candidats_dict=candidats_dict)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
