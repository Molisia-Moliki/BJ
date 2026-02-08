from discord import app_commands
from discord.ext import commands
import random
import json
import os

COLLECTION_FILE = "collection.json"
cards = [
    {"name": "Sakura", "anime": "Naruto", "rarity": "Ultra Rare", "img": "https://i.imgur.com/abcd.png"},
    {"name": "Rem", "anime": "Re:Zero", "rarity": "Rare", "img": "https://i.imgur.com/efgh.png"}
]

def load_collection():
    if not os.path.exists(COLLECTION_FILE):
        return {}
    with open(COLLECTION_FILE, "r") as f:
        return json.load(f)

def save_collection(data):
    with open(COLLECTION_FILE, "w") as f:
        json.dump(data, f, indent=4)

def setup(bot):
    @bot.tree.command(name="draw", description="Losuj kartę anime")
    async def draw(interaction: commands.Context):
        collection = load_collection()
        uid = str(interaction.user.id)
        if uid not in collection:
            collection[uid] = []
        card = random.choice(cards)
        collection[uid].append(card)
        save_collection(collection)
        await interaction.response.send_message(f"Twoja karta: {card['name']} ({card['rarity']}) z anime {card['anime']}")
