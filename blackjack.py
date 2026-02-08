import discord
from discord import app_commands
import random
import asyncio
from economy import get_player, save_players

# ---------- KARTY ----------
suits = ["♠", "♥", "♦", "♣"]
values = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def draw_card():
    return f"{random.choice(list(values.keys()))}{random.choice(suits)}"

def hand_value(hand):
    total = 0
    aces = 0
    for card in hand:
        v = card[:-1]
        total += values[v]
        if v == "A":
            aces += 1
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def hand_text(hand):
    return " ".join(hand)

# ---------- VIEW ----------
class BlackjackView(discord.ui.View):
    def __init__(self, interaction, game):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.game = game

    async def interaction_check(self, interaction):
        return interaction.user.id == self.interaction.user.id

    def build_embed(self, reveal=False, end=False, result=None, color=discord.Color.green()):
        if reveal:
            dealer_hand = hand_text(self.game["dealer"])
            dealer_value = f"**({hand**_
