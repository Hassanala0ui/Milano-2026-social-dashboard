import json
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from neo4j import GraphDatabase

# ==========================================
# 1. CONFIGURATION ET CHARGEMENT
# ==========================================
load_dotenv()

# Assure-toi que le nom du fichier est correct (j'ai mis milano_data.json)
FICHIER_DONNEES = 'milano_data.json'

try:
    with open(FICHIER_DONNEES, 'r', encoding='utf-8') as file:
        data = json.load(file)
    print(f"✅ Données chargées depuis {FICHIER_DONNEES} !")
except FileNotFoundError:
    print(f"❌ Erreur : Le fichier {FICHIER_DONNEES} est introuvable.")
    sys.exit(1)

# ==========================================
# PARTIE MONGODB : La base "Documents"
# ==========================================
print("\n🔄 Connexion à MongoDB...")
try:
    mongo_client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping') # Test la connexion
    
    db = mongo_client["milano2026"]

    # Nettoyage
    db.users.drop()
    db.tweets.drop()

    # Insertion massive
    db.users.insert_many(data["users"])
    db.tweets.insert_many(data["tweets"])
    
    # BONUS PRO : Création d'index pour accélérer les futures requêtes
    db.users.create_index("user_id", unique=True)
    db.tweets.create_index("tweet_id", unique=True)

    print(f"✅ MongoDB : {db.users.count_documents({})} utilisateurs et {db.tweets.count_documents({})} tweets insérés.")
except Exception as e:
    print(f"❌ Erreur de connexion MongoDB : {e}")


# ==========================================
# PARTIE NEO4J : La base "Graphe"
# ==========================================
print("\n🔄 Connexion à Neo4j...")
try:
    neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    neo4j_driver.verify_connectivity()

    # ACTION 1 : Créer les contraintes dans une transaction séparée
    def setup_constraints(tx):
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
        tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tweet) REQUIRE t.tweet_id IS UNIQUE")

    # ACTION 2 : Insérer les données
    def seed_graph(tx, data):
        # Nettoyage complet
        tx.run("MATCH (n) DETACH DELETE n")
        
        # Création des Utilisateurs
        tx.run("""
            UNWIND $users AS user
            CREATE (:User {user_id: user.user_id, username: user.username, role: user.role})
        """, users=data["users"])

        # Création des Tweets et relations AUTHORED
        tx.run("""
            UNWIND $tweets AS tweet
            MATCH (u:User {user_id: tweet.user_id})
            CREATE (t:Tweet {tweet_id: tweet.tweet_id})
            CREATE (u)-[:AUTHORED]->(t)
        """, tweets=data["tweets"])

        # Création des relations REPLY_TO
        tx.run("""
            UNWIND $tweets AS tweet
            WITH tweet WHERE tweet.in_reply_to_tweet_id IS NOT NULL
            MATCH (t1:Tweet {tweet_id: tweet.tweet_id})
            MATCH (t2:Tweet {tweet_id: tweet.in_reply_to_tweet_id})
            CREATE (t1)-[:REPLY_TO]->(t2)
        """, tweets=data["tweets"])

        # Création des relations FOLLOWS
        tx.run("""
            UNWIND $follows AS follow
            MATCH (u1:User {user_id: follow.follower_id})
            MATCH (u2:User {user_id: follow.followed_id})
            CREATE (u1)-[:FOLLOWS]->(u2)
        """, follows=data["follows"])

        # Création des relations RETWEETS
        tx.run("""
            UNWIND $retweets AS retweet
            MATCH (u:User {user_id: retweet.user_id})
            MATCH (t:Tweet {tweet_id: retweet.tweet_id})
            CREATE (u)-[:RETWEETS]->(t)
        """, retweets=data["retweets"])

    # Exécution des deux actions séparément !
    with neo4j_driver.session() as session:
        session.execute_write(setup_constraints)
        
        # ---> LE NETTOYAGE EST ICI <---
        # On supprime les _id ajoutés par MongoDB avant d'envoyer à Neo4j
        for user in data["users"]:
            user.pop("_id", None)
        for tweet in data["tweets"]:
            tweet.pop("_id", None)
        # ------------------------------
        
        session.execute_write(seed_graph, data)
        
    print("✅ Neo4j : Nœuds et relations créés avec succès (optimisé avec UNWIND) !")

except Exception as e:
    print(f"❌ Erreur Neo4j : {e}")
finally:
    if 'neo4j_driver' in locals():
        neo4j_driver.close()

print("\n🚀 Terminé ! Le jeu de données est en place.")