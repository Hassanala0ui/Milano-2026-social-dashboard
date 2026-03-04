import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone

# --- 1. CONFIGURATION ---
load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["milano2026"]

# ==========================================
# 2. CRUD : UTILISATEURS (users)
# ==========================================

def insert_user(user_id, username, role, country):
    """Insère un nouvel utilisateur dans la collection 'users'."""
    nouveau_user = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "country": country,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    resultat = db.users.insert_one(nouveau_user)
    print(f"✅ Utilisateur '{username}' inséré avec l'ID interne: {resultat.inserted_id}")

def update_user(user_id, champs_a_modifier):
    """Met à jour les informations d'un utilisateur existant."""
    resultat = db.users.update_one(
        {"user_id": user_id},
        {"$set": champs_a_modifier}
    )
    if resultat.modified_count > 0:
        print(f"🔄 Utilisateur {user_id} mis à jour avec succès.")
    else:
        print(f"⚠️ Aucun utilisateur modifié (L'utilisateur {user_id} n'existe pas ou les données sont identiques).")

def delete_user(user_id):
    """Supprime un utilisateur de la base de données."""
    resultat = db.users.delete_one({"user_id": user_id})
    if resultat.deleted_count > 0:
        print(f"❌ Utilisateur {user_id} supprimé de la base.")
    else:
        print(f"⚠️ Utilisateur {user_id} introuvable.")

# ==========================================
# 3. CRUD : TWEETS (tweets)
# ==========================================

def insert_tweet(tweet_id, user_id, text, hashtags, in_reply_to=None):
    """Insère un nouveau tweet dans la collection 'tweets'."""
    nouveau_tweet = {
        "tweet_id": tweet_id,
        "user_id": user_id,
        "text": text,
        "hashtags": hashtags,
        "favorite_count": 0, # Commence à 0 like
        "in_reply_to_tweet_id": in_reply_to,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    resultat = db.tweets.insert_one(nouveau_tweet)
    print(f"✅ Tweet '{tweet_id}' publié par '{user_id}'.")

def update_tweet(tweet_id, champs_a_modifier):
    """Met à jour un tweet existant (par exemple, ajouter des likes)."""
    resultat = db.tweets.update_one(
        {"tweet_id": tweet_id},
        {"$set": champs_a_modifier}
    )
    if resultat.modified_count > 0:
        print(f"🔄 Tweet {tweet_id} mis à jour.")
    else:
        print(f"⚠️ Tweet {tweet_id} introuvable ou identique.")

def delete_tweet(tweet_id):
    """Supprime un tweet de la base de données."""
    resultat = db.tweets.delete_one({"tweet_id": tweet_id})
    if resultat.deleted_count > 0:
        print(f"❌ Tweet {tweet_id} supprimé.")
    else:
        print(f"⚠️ Tweet {tweet_id} introuvable.")


# ==========================================
# 4. ZONE DE TEST (Démonstration)
# ==========================================
if __name__ == "__main__":
    print("--- DÉBUT DU TEST CRUD MONGODB ---")
    
    # 1. Tester la création (Create)
    insert_user("U999", "Test_User", "fan", "France")
    insert_tweet("T999", "U999", "Ceci est un test CRUD ! #Test", ["Test"])
    
    # 2. Tester la mise à jour (Update)
    update_user("U999", {"role": "vip", "country": "Italy"})
    update_tweet("T999", {"favorite_count": 42})
    
    # 3. Tester la suppression (Delete)
    # (Décommente les lignes ci-dessous si tu veux vraiment les supprimer après le test)
    # delete_tweet("T999")
    # delete_user("U999")
    
    print("--- FIN DU TEST ---")