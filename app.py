import os
import pandas as pd
from flask import Flask, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 🔹 Chargement du modèle
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Chargement des phrases de référence
def charger_phrases_reference(fichier=None):
    if fichier is None:
        fichier = os.path.join(app.root_path, "analys.txt")
    phrases = []
    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                if "   " in ligne:
                    ligne = ligne.rsplit("   ", 1)[0]
                phrases.append(ligne)
    return phrases

phrases_ref = charger_phrases_reference()
embeddings_ref = model.encode(phrases_ref)

# 🔹 Route principale : affiche une offre
@app.route("/")
def home():
    try:
        with open(os.path.join(app.root_path, "analys.txt"), "r", encoding="utf-8") as f:
            premiere_phrase = f.readline().strip()
    except Exception:
        premiere_phrase = "Pas de description disponible."

    return render_template("home.html", description=premiere_phrase)

# 🔹 Route analyse
@app.route("/analyze/")
def analyze():
    try:
        with open(os.path.join(app.root_path, "analys.txt"), "r", encoding="utf-8") as f:
            phrase_ref = f.readline().strip()
    except Exception:
        phrase_ref = ""

    try:
        df = pd.read_csv("resume_data.csv").sample(n=10)
        df = df.dropna(subset=["career_objective"])  # 🔸 Supprime les lignes sans texte
        textes = df["career_objective"].astype(str).tolist()
        emb_obj = model.encode(textes)
        emb_ref = model.encode([phrase_ref])
        scores = cosine_similarity(emb_obj, emb_ref).flatten()
        df["similarity"] = scores
        df = df.sort_values("similarity", ascending=False)
        resultats = df[["career_objective", "similarity"]].values.tolist()
    except Exception as e:
        resultats = []

    return render_template("analyze.html", best_phrase=phrase_ref, table=resultats)


