import os
from flask import Flask, render_template, request
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2

# Initialisation
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Modèle
model = SentenceTransformer("all-MiniLM-L6-v2")

# Chargement des phrases de référence (CV ou fichier de phrases)
def charger_phrases_reference(fichier="/Users/eliot/Desktop/data_apps_project/analys.txt"):
    phrases = []
    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                # Enlève le label éventuel s'il y en a
                if "   " in ligne:
                    ligne = ligne.rsplit("   ", 1)[0]
                phrases.append(ligne)
    return phrases

phrases_ref = charger_phrases_reference()
embeddings_ref = model.encode(phrases_ref)

# Fonction pour lire texte du PDF
def lire_pdf(path):
    texte = ""
    with open(path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            texte += page.extract_text() or ""
    return texte.strip()

@app.route("/", methods=["GET", "POST"])
def home():
    meilleur_score = None
    meilleure_phrase = None
    texte_pdf = ""

    if request.method == "POST":
        fichier = request.files["pdf_file"]
        if fichier.filename.endswith(".pdf"):
            path_pdf = os.path.join(app.config["UPLOAD_FOLDER"], fichier.filename)
            fichier.save(path_pdf)

            # Lire le texte du PDF
            texte_pdf = lire_pdf(path_pdf)
            emb_pdf = model.encode(texte_pdf)

            # Calculer les similarités
            scores = cosine_similarity([emb_pdf], embeddings_ref)[0]
            idx_best = scores.argmax()
            meilleur_score = scores[idx_best]
            meilleure_phrase = phrases_ref[idx_best]

    return render_template(
        "home.html",
        score=meilleur_score,
        best_phrase=meilleure_phrase,
        texte_pdf=texte_pdf[:500]
    )

@app.route("/analyse")
def nav_to_analyse():
    return render_template("analyse.html")

if __name__ == "__main__" and os.getenv("ENV") == "dev":
    app.run(debug=True)

