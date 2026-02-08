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
        super().__init__(timeout=120)  # 2 min timeout
        self.interaction = interaction
        self.game = game

    async def interaction_check(self, interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    def build_embed(self, reveal=False, end=False, result=None, color=discord.Color.green()):
        if reveal:
            dealer_hand = hand_text(self.game["dealer"])
            dealer_value = f"**({hand_value(self.game['dealer'])})**"
        else:
            dealer_hand = f"{self.game['dealer'][0]} ❓"
            dealer_value = ""

        embed = discord.Embed(
            title="🃏 BlackJack",
            color=color
        )
        embed.add_field(
            name="👤 Twoje karty",
            value=f"{hand_text(self.game['player'])}\n**({hand_value(self.game['player'])})**",
            inline=False
        )
        embed.add_field(
            name="🎩 Krupier",
            value=f"{dealer_hand}\n{dealer_value}",
            inline=False
        )
        embed.add_field(
            name="💰 Zakład",
            value=str(self.game["bet"]),
            inline=True
        )
        embed.add_field(
            name="💳 Saldo",
            value=str(get_player(self.interaction.user.id)["balance"]),
            inline=True
        )

        if end and result:
            embed.add_field(name="📢 Wynik", value=result, inline=False)
        return embed

    async def animated_draw(self, interaction, target):
        loading = discord.Embed(title="🎴 Dobieranie karty...", color=discord.Color.blue())
        try:
            await interaction.response.edit_message(embed=loading, view=None)
        except discord.NotFound:
            return
        await asyncio.sleep(0.8)

        self.game[target].append(draw_card())

        try:
            await interaction.edit_original_response(embed=self.build_embed(), view=self)
        except discord.NotFound:
            pass

    async def finish(self, interaction):
        dealer = self.game["dealer"]
        p = get_player(interaction.user.id)

        while hand_value(dealer) < 17:
            await asyncio.sleep(0.6)
            dealer.append(draw_card())

        pv = hand_value(self.game["player"])
        dv = hand_value(dealer)
        bet = self.game["bet"]
        p["games"] += 1

        if dv > 21 or pv > dv:
            p["balance"] += bet
            p["wins"] += 1
            result = f"🎉 Wygrana +{bet}"
