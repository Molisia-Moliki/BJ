import random
import json
import os

COLLECTION_FILE = "collection.json"

# ---------- KARTY ----------
cards = [
    {"name": "Sakura", "anime": "Naruto", "rarity": "Ultra Rare", "img": "https://i.imgur.com/abcd.png"},
    {"name": "Rem", "anime": "Re:Zero", "rarity": "Rare", "img": "https://i.imgur.com/efgh.png"},
    {"name": "Miku Hatsune", "anime": "Vocaloid", "rarity": "Normal", "img": "https://i.imgur.com/ijkl.png"},
    {"name": "Nezuko", "anime": "Demon Slayer", "rarity": "Rare", "img": "https://i.imgur.com/mnop.png"},
    {"name": "Zero Two", "anime": "Darling in the Franxx", "rarity": "Ultra Rare", "img": "https://i.imgur.com/qrst.png"}
]

# ---------- DANE GRACZY ----------
def load_collection():
    if not os.path.exists(COLLECTION_FILE):
        return {}
    with open(COLLECTION_FILE, "r") as f:
        return json.load(f)

def save_collection(data):
    with open(COLLECTION_FILE, "w") as f:
        json.dump(data, f, indent=4)

collection = load_collection()

def get_player(uid):
    uid = str(uid)
    if uid not in collection:
        collection[uid] = []
    return collection[uid]

# ---------- LOGIKA GRY ----------
class AnimeCardGame:
    def __init__(self, user_id):
        self.user_id = str(user_id)
        self.player_cards = get_player(user_id)

    def draw(self):
        card = random.choice(cards)
        self.player_cards.append(card)
        collection[self.user_id] = self.player_cards
        save_collection(collection)
        return card

    def get_collection(self, limit=None):
        """Zwraca kolekcję gracza. Limit = ilość ostatnich kart"""
        if limit:
            return self.player_cards[-limit:]
        return self.player_cards
