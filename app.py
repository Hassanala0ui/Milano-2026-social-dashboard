import os
import tkinter as tk
from tkinter import scrolledtext
from dotenv import load_dotenv
from pymongo import MongoClient
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
from pyvis.network import Network
import webbrowser
from textblob import TextBlob

# --- 1. CONFIGURATION DB ---
load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["milano2026"]

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

# --- 2. FONCTIONS OUTILS ---
def log(message):
    """Ajoute du texte dans la zone d'affichage de l'interface."""
    text_area.insert(tk.END, message + "\n")
    text_area.yview(tk.END)

def run_neo4j_query(query, parameters=None):
    """Exécute une requête Neo4j et retourne les résultats."""
    with neo4j_driver.session() as session:
        result = session.run(query, parameters)
        return [record.data() for record in result]

# --- 3. FONCTIONS DES BOUTONS ---
def run_stats():
    """Exécute les 16 questions obligatoires et affiche les résultats dans l'UI."""
    text_area.delete(1.0, tk.END) # Efface l'écran avant de lancer
    log("="*50)
    log("🏆 RÉPONSES AUX 16 QUESTIONS OBLIGATOIRES 🏆")
    log("="*50)
    
    # ---------------------------------------------------------
    log("\n🔹 PARTIE MONGODB (Statistiques & Contenu)")
    # ---------------------------------------------------------
    q1 = db.users.count_documents({})
    log(f"Q1. Nombre d'utilisateurs : {q1}")
    
    q2 = db.tweets.count_documents({})
    log(f"Q2. Nombre de tweets : {q2}")
    
    q3 = len(db.tweets.distinct("hashtags"))
    log(f"Q3. Nombre de hashtags distincts : {q3}")
    
    q4 = db.tweets.count_documents({"hashtags": {"$regex": "Milano2026", "$options": "i"}})
    log(f"Q4. Tweets contenant #Milano2026 : {q4}")
    
    q5 = len(db.tweets.distinct("user_id", {"hashtags": {"$regex": "milano2026", "$options": "i"}}))
    log(f"Q5. Utilisateurs distincts ayant utilisé #Milano2026 : {q5}")
    
    q6 = list(db.tweets.find({"in_reply_to_tweet_id": {"$ne": None}}, {"_id": 0, "tweet_id": 1}))
    log(f"Q6. Nombre de tweets qui sont des réponses : {len(q6)}")
    
    log("\nQ12. Les 10 tweets les plus populaires :")
    q12 = db.tweets.find({}, {"_id": 0, "tweet_id": 1, "favorite_count": 1}).sort("favorite_count", -1).limit(10)
    for i, t in enumerate(q12, 1):
        log(f"  {i}. {t['tweet_id']} ({t['favorite_count']} likes)")
        
    log("\nQ13. Les 10 hashtags les plus populaires :")
    q13 = list(db.tweets.aggregate([
        {"$unwind": "$hashtags"},
        {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]))
    for i, h in enumerate(q13, 1):
        log(f"  {i}. {h['_id']} ({h['count']} apparitions)")

    # ---------------------------------------------------------
    log("\n🔹 PARTIE NEO4J (Réseau & Discussions)")
    # ---------------------------------------------------------
    q7 = run_neo4j_query("MATCH (u:User)-[:FOLLOWS]->(m:User {username: 'Milano Ops'}) RETURN u.username AS follower")
    log(f"Q7. Followers de MilanoOps ({len(q7)}) : {[r['follower'] for r in q7[:5]]}...")
    
    q8 = run_neo4j_query("MATCH (m:User {username: 'Milano Ops'})-[:FOLLOWS]->(u:User) RETURN u.username AS followed")
    log(f"Q8. Suivis par MilanoOps ({len(q8)}) : {[r['followed'] for r in q8]}")
    
    q9 = run_neo4j_query("MATCH (m:User {username: 'Milano Ops'})-[:FOLLOWS]->(u:User)-[:FOLLOWS]->(m) RETURN u.username AS mutual")
    log(f"Q9. Relations réciproques avec MilanoOps : {[r['mutual'] for r in q9]}")
    
    q10 = run_neo4j_query("MATCH (u:User)<-[:FOLLOWS]-(f:User) WITH u, count(f) AS followers_count WHERE followers_count > 10 RETURN u.username AS username, followers_count ORDER BY followers_count DESC")
    log("\nQ10. Utilisateurs avec plus de 10 followers :")
    for r in q10: log(f"  - {r['username']} ({r['followers_count']} followers)")
    
    q11 = run_neo4j_query("MATCH (u:User)-[:FOLLOWS]->(f:User) WITH u, count(f) AS following_count WHERE following_count > 5 RETURN u.username AS username, following_count ORDER BY following_count DESC")
    log("\nQ11. Utilisateurs qui suivent plus de 5 personnes :")
    for r in q11: log(f"  - {r['username']} (suit {r['following_count']} personnes)")
    
    q14 = run_neo4j_query("MATCH (reply:Tweet)-[:REPLY_TO]->(t:Tweet) WHERE NOT (t)-[:REPLY_TO]->() RETURN DISTINCT t.tweet_id AS starter")
    log(f"\nQ14. Tweets initiant une discussion : {[r['starter'] for r in q14]}")
    
    q15 = run_neo4j_query("MATCH p = (leaf:Tweet)-[:REPLY_TO*]->(root:Tweet) WHERE NOT ()-[:REPLY_TO]->(leaf) AND NOT (root)-[:REPLY_TO]->() RETURN [x in nodes(p) | x.tweet_id] AS thread, length(p) AS longueur ORDER BY longueur DESC LIMIT 1")
    if q15:
        log(f"Q15. Discussion la plus longue (taille {q15[0]['longueur']}) : {' -> '.join(reversed(q15[0]['thread']))}")
        
    q16 = run_neo4j_query("MATCH p = (leaf:Tweet)-[:REPLY_TO*]->(root:Tweet) WHERE NOT ()-[:REPLY_TO]->(leaf) AND NOT (root)-[:REPLY_TO]->() RETURN root.tweet_id AS debut, leaf.tweet_id AS fin")
    log(f"\nQ16. Début et fin des conversations (Aperçu) :")
    for r in q16[:5]: log(f"  Début: {r['debut']} | Fin: {r['fin']}")
    
    log("\n✅ Analyse terminée avec succès !")
    log("="*50 + "\n")

def show_mongo_chart():
    """Génère un graphique Matplotlib (Top 10 Hashtags)."""
    log("📈 Ouverture du graphique des hashtags (Matplotlib)...")
    pipeline = [
        {"$unwind": "$hashtags"},
        {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    data = list(db.tweets.aggregate(pipeline))
    
    labels = [item['_id'] for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(10, 5))
    plt.bar(labels, counts, color='skyblue')
    plt.title('Top 10 des Hashtags - Milano-Cortina 2026')
    plt.xlabel('Hashtags')
    plt.ylabel('Nombre de tweets')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def show_neo4j_graph():
    """Génère un graphe interactif Pyvis autour de Milano Ops."""
    log("🕸️ Génération de la carte Neo4j dans le navigateur...")
    
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    
    with neo4j_driver.session() as session:
        query = """
        MATCH (u1:User)-[r:FOLLOWS]->(u2:User)
        WHERE u1.username = 'Milano Ops' OR u2.username = 'Milano Ops'
        RETURN u1.username AS source, u2.username AS target
        """
        results = session.run(query)
        
        for record in results:
            src = record["source"]
            tgt = record["target"]
            net.add_node(src, label=src, color="orange" if src == "Milano Ops" else "lightblue")
            net.add_node(tgt, label=tgt, color="orange" if tgt == "Milano Ops" else "lightblue")
            net.add_edge(src, tgt, title="FOLLOWS")
    
    file_name = "reseau_milano.html"
    net.write_html(file_name)
    webbrowser.open('file://' + os.path.realpath(file_name))
    log("✅ Carte du réseau ouverte !")

def on_closing():
    """Ferme proprement les connexions."""
    neo4j_driver.close()
    root.destroy()

def show_sentiment_analysis():
    """Bonus IA : Analyse de sentiments des tweets avec TextBlob et MongoDB."""
    log("🧠 Lancement de l'IA (Analyse de sentiments)...")
    
    # Étape A : L'IA récupère tous les textes des tweets depuis MongoDB
    tweets = db.tweets.find({}, {"_id": 0, "text": 1})
    
    positif, negatif, neutre = 0, 0, 0
    
    # Étape B : L'IA lit et note chaque tweet
    for t in tweets:
        texte = t.get("text", "")
        # TextBlob analyse le texte et donne un score de polarité
        score = TextBlob(texte).sentiment.polarity
        
        if score > 0.1:
            positif += 1
        elif score < -0.1:
            negatif += 1
        else:
            neutre += 1
            
    # Étape C : Création du graphique en camembert (Pie Chart)
    labels = ['Positifs 😊', 'Neutres 😐', 'Négatifs 😠']
    tailles = [positif, neutre, negatif]
    couleurs = ['#a2d149', '#e0e0e0', '#ff6b6b']
    
    plt.figure(figsize=(8, 6))
    plt.pie(tailles, labels=labels, colors=couleurs, autopct='%1.1f%%', startangle=90, explode=(0.05, 0.05, 0.05))
    plt.title("IA : Analyse des Sentiments - JO Milano-Cortina 2026", fontweight='bold', fontsize=14)
    plt.tight_layout()
    
    log(f"✅ IA terminée : {positif} Positifs, {neutre} Neutres, {negatif} Négatifs.")
    plt.show()


# --- 4. CRÉATION DE L'INTERFACE TKINTER ---
root = tk.Tk()
root.title("Tableau de Bord - JO Milano-Cortina 2026")
root.geometry("800x600")
root.protocol("WM_DELETE_WINDOW", on_closing)

frame_buttons = tk.Frame(root, padx=10, pady=10)
frame_buttons.pack(side=tk.LEFT, fill=tk.Y)

lbl_title = tk.Label(frame_buttons, text="Outils d'analyse", font=("Arial", 14, "bold"))
lbl_title.pack(pady=10)

btn_stats = tk.Button(frame_buttons, text="1. Lancer les 16 Requêtes", width=25, command=run_stats, bg="#d9ead3")
btn_stats.pack(pady=5)

btn_chart = tk.Button(frame_buttons, text="2. Graphique Hashtags\n(Matplotlib)", width=25, command=show_mongo_chart)
btn_chart.pack(pady=5)

btn_graph = tk.Button(frame_buttons, text="3. Réseau Neo4j\n(Pyvis)", width=25, command=show_neo4j_graph)
btn_graph.pack(pady=5)

btn_ia = tk.Button(frame_buttons, text="4. Analyse Sentiments", width=25, command=show_sentiment_analysis, bg="#ffe599")
btn_ia.pack(pady=5)

btn_quit = tk.Button(frame_buttons, text="Quitter", width=25, fg="red", command=on_closing)
btn_quit.pack(side=tk.BOTTOM, pady=10)

frame_text = tk.Frame(root, padx=10, pady=10)
frame_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

text_area = scrolledtext.ScrolledText(frame_text, wrap=tk.WORD, font=("Consolas", 10))
text_area.pack(fill=tk.BOTH, expand=True)

log("Bienvenue sur le tableau de bord Milano-Cortina 2026.")
log("Cliquez sur le bouton vert à gauche pour générer les réponses aux 16 questions obligatoires.\n")

root.mainloop()