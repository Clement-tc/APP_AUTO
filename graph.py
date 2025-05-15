import matplotlib.pyplot as plt

try:
    # Charger les données
    df = pd.read_csv("resume_data.csv")
    df = df.dropna(subset=["matched_score"])

    # Convertir les scores en float (si nécessaire)
    df["matched_score"] = df["matched_score"].astype(float)

    # 🔹 Génération du graphique
    plt.figure(figsize=(10, 6))
    plt.hist(df["matched_score"], bins=20, color='blue', alpha=0.7, edgecolor='black')
    plt.title("Distribution des scores de correspondance (matched_score)")
    plt.xlabel("Score de correspondance")
    plt.ylabel("Nombre de CV")
    plt.show()
except Exception as e:
    print(f"Erreur lors de la génération du graphique : {e}")

# 🔹 Chargement des données
try:
    # Charger les données
    df = pd.read_csv("resume_data.csv")

    # Vérifier si la colonne existe
    if "experiencere_requirement" not in df.columns:
        raise ValueError("La colonne 'experiencere_requirement' n'existe pas dans le dataset.")

    # Remplacer les valeurs manquantes par "Non spécifié"
    df["experiencere_requirement"] = df["experiencere_requirement"].fillna("Non spécifié")
    experience_data = df["experiencere_requirement"].astype(str)

    # 🔹 Génération du graphique
    plt.figure(figsize=(10, 6))
    experience_data.value_counts().plot(kind="bar", color="blue", alpha=0.7, edgecolor="black")
    plt.title("Distribution des expériences requises")
    plt.xlabel("Expérience requise")
    plt.ylabel("Nombre d'occurrences")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    plt.show()
except Exception as e:
    print(f"Erreur lors de la génération du graphique : {e}")