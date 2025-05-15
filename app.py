import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib
matplotlib.use('Agg')  # Utiliser un backend non interactif pour éviter l'erreur
import matplotlib.pyplot as plt
import io  # Ajout de l'importation du module io
import base64
import numpy as np
import fitz

# Initialisation de Flask et de la base de données
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offres_emploi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'votre_cle_secrete'  # Nécessaire pour les sessions de Flask
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialisation du modèle de transformation
model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialisation de Flask-Login pour la gestion des utilisateurs
login_manager = LoginManager()
login_manager.init_app(app)

# Fonction de chargement de l'utilisateur
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modèle pour les utilisateurs (Candidat ou Recruteur)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'recruteur' ou 'candidat'

# Modèle pour les offres d'emploi
class OffreEmploi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    localisation = db.Column(db.String(100), nullable=False)
    competences = db.Column(db.String(200), nullable=False)
    date_publication = db.Column(db.String(50), nullable=False)

# Modèle pour les candidats qui postulent
class Candidat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    cv = db.Column(db.String(3000), nullable=False)  # Le chemin vers le fichier CV
    offre_id = db.Column(db.Integer, db.ForeignKey('offre_emploi.id'), nullable=False)
    offre = db.relationship('OffreEmploi', backref=db.backref('candidats', lazy=True))
    date_postulation = db.Column(db.String(50), nullable=False)

# Fonction pour extraire et concaténer 'skills' et 'career_objective' des CV
def get_cv_text(df):
    return df['skills'] + " " + str(df['career_objective'])

# Créer la base de données si elle n'existe pas
with app.app_context():
    db.create_all()

    # Vérifier s'il y a des offres dans la base de données, sinon ajouter les offres fictives
    if OffreEmploi.query.count() == 0:
        offres = [
            OffreEmploi(
                titre="Analytics Engineer",
                description="""Notre équipe Data recherche son / sa futur(e) stagiaire sur une fonction d’Analytics Engineer et ainsi développer une puissante infrastructure capable de supporter les données issues de nos produits...""",
                localisation="Paris",
                competences="Airflow, AWS, Data Engineering, Python",
                date_publication="2025-05-01"
            ),
            OffreEmploi(
                titre="Data Analyst",
                description="""Analyser et visualiser les données pour prendre des décisions stratégiques...""",
                localisation="Lyon",
                competences="SQL, Tableau, Python",
                date_publication="2025-05-02"
            ),
            OffreEmploi(
                titre="Data Engineer",
                description="""Construire et maintenir des pipelines de données pour collecter, transformer et stocker les données provenant de différentes sources...""",
                localisation="Marseille",
                competences="Python, SQL, Hadoop, Spark",
                date_publication="2025-05-03"
            ),
            OffreEmploi(
                titre="Machine Learning Engineer",
                description="""Développer des modèles d'apprentissage automatique pour automatiser l'analyse des données...""",
                localisation="Bordeaux",
                competences="Python, TensorFlow, Kubernetes",
                date_publication="2025-05-04"
            )
        ]
        db.session.add_all(offres)
        db.session.commit()  # Commiter les offres à la base de données

    # Ajouter des candidatures simulées basées sur l'échantillon du CSV
        df = pd.read_csv('resume_data.csv')  # Charger les données depuis le fichier CSV
        for offre in offres:
            candidats_postules = Candidat.query.filter_by(offre_id=offre.id).all()
            if len(candidats_postules) == 0:
                for _, row in df.sample(n=np.random.randint(1, 10)).iterrows():
                    cv_text = get_cv_text(row)  # Concaténer 'skills' et 'career_objective'
                    
                    # Ajouter un candidat avec un score similaire
                    candidat = Candidat(nom=str(_), cv=cv_text, offre_id=offre.id, date_postulation="2025-05-06")
                    db.session.add(candidat)
                    db.session.commit()  # Commiter chaque candidat

# Route principale : afficher les offres d'emploi
@app.route("/")
def home():
    offres = OffreEmploi.query.all()  # Récupérer toutes les offres depuis la base de données
    return render_template("home.html", offres=offres)

# Route pour la connexion
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            if user.role == 'recruteur':
                return redirect(url_for('home'))  # Rediriger vers la page d'accueil des recruteurs
            else:
                return redirect(url_for('postuler'))  # Rediriger vers la page de postulation pour les candidats
    return render_template("login.html")

# Route pour la déconnexion
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Route pour postuler à une offre d'emploi (uniquement pour candidats)
@app.route("/postuler/<int:offre_id>", methods=["GET", "POST"])
@login_required
def postuler(offre_id):
    if current_user.role != 'candidat':
        return redirect(url_for('home'))  # Si l'utilisateur n'est pas un candidat, redirige vers l'accueil
    
    offre = OffreEmploi.query.get_or_404(offre_id)

    if request.method == "POST":
        nom = request.form['nom']
        cv_file = request.files['cv']

        # Sauvegarder le fichier CV
        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], cv_file.filename)
        cv_file.save(cv_path)
        cv_text = extract_text_from_pdf(cv_path)

        # Ajouter le candidat à la base de données
        candidat = Candidat(nom=nom, cv=cv_text, offre_id=offre_id, date_postulation="2025-05-06")
        db.session.add(candidat)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("postuler.html", offre=offre)



# Fonction pour extraire le texte d'un fichier PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()  # Extraire le texte de chaque page
    return text

# Fonction pour lire le contenu d'un fichier texte (.txt)
def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        return file.read()

@app.route("/analyze/<int:offre_id>")
@login_required
def analyze(offre_id):
    if current_user.role != 'recruteur':
        return redirect(url_for('home'))  # Si l'utilisateur n'est pas un recruteur, redirige vers l'accueil
    
    offre = OffreEmploi.query.get_or_404(offre_id)
    candidats = Candidat.query.filter_by(offre_id=offre_id).all()  # Récupérer les candidats pour cette offre
    resultats = []

    for candidat in candidats:
        cv_text = candidat.cv


        # Calculer la similarité entre le texte du CV et la description de l'offre
        emb_obj = model.encode([cv_text])
        emb_ref = model.encode([offre.description])
        score = cosine_similarity(emb_obj, emb_ref).flatten()[0]
        
        resultats.append((candidat.nom, score))  # Ajouter le résultat à la liste
    # Trier les résultats par similarité
    resultats = sorted(resultats, key=lambda x: x[1], reverse=True)

    # Création du graphique
    fig, ax = plt.subplots()
    ax.plot(range(len(resultats)), [x[1] for x in resultats], marker='o', linestyle='-', color='b')
    ax.set_title('Graphique des scores de similarité')
    ax.set_xlabel('Candidats')
    ax.set_ylabel('Score de Similarité')

    # Convertir le graphique en image base64
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode()

    # Calculer la moyenne des scores
    moyenne_score = sum([x[1] for x in resultats]) / len(resultats) if resultats else 0

    return render_template("analyze.html", offre=offre, table=resultats, moyenne_score=moyenne_score, img_base64=img_base64)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Vérifier si l'utilisateur existe déjà
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return "Utilisateur déjà existant. Veuillez vous connecter."

        # Créer un nouvel utilisateur
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        # Connecter l'utilisateur après l'inscription
        login_user(user)

        return redirect(url_for('home'))  # Rediriger vers la page d'accueil après inscription

    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)
