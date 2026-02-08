import discord
from discord import app_commands
import random
import asyncio
from economy import get_player, save_players  # upewnij się, że masz economy.py z funkcjami get_player/save_players

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
            embed.add_field(
                name="📢 Wynik",
                value=result,
                inline=False
            )

        return embed

    async def animated_draw(self, interaction, target):
        loading = discord.Embed(
            title="🎴 Dobieranie karty...",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=loading, view=None)
        await asyncio.sleep(0.8)

        self.game[target].append(draw_card())

        await interaction.edit_original_response(
            embed=self.build_embed(),
            view=self
        )

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
            color = discord.Color.purple()
        elif pv < dv:
            p["balance"] -= bet
            p["losses"] += 1
            result = f"💀 Przegrana -{bet}"
            color = discord.Color.red()
        else:
            p["draws"] += 1
            result = "🤝 Remis"
            color = discord.Color.gold()

        save_players()
        self.stop()

        await interaction.edit_original_response(
            embed=self.build_embed(
                reveal=True,
                end=True,
                result=result,
                color=color
            ),
            view=None
        )

    @discord.ui.button(label="🎴 Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction, button):
        await self.animated_draw(interaction, "player")
        if hand_value(self.game["player"]) > 21:
            p = get_player(interaction.user.id)
            p["balance"] -= self.game["bet"]
            p["losses"] += 1
            p["games"] += 1
            save_players()
            self.stop()

            await interaction.edit_original_response(
                embed=self.build_embed(
                    reveal=True,
                    end=True,
                    result="💥 Bust!",
                    color=discord.Color.red()
                ),
                view=None
            )

    @discord.ui.button(label="✋ Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction, button):
        await self.finish(interaction)

    @discord.ui.button(label="💸 Double", style=discord.ButtonStyle.blurple)
    async def double(self, interaction, button):
        p = get_player(interaction.user.id)
        if p["balance"] < self.game["bet"]:
            await interaction.response.send_message(
                "❌ Brak środków",
                ephemeral=True
            )
            return

        self.game["bet"] *= 2
        await self.animated_draw(interaction, "player")
        await self.finish(interaction)

# ---------- SETUP ----------
def setup(bot):
    @bot.tree.command(name="blackjack", description="Zagraj w BlackJacka")
    @app_commands.describe(bet="Kwota zakładu")
    async def blackjack(interaction: discord.Interaction, bet: int):
        p = get_player(interaction.user.id)

        if bet <= 0 or bet > p["balance"]:
            await interaction.response.send_message(
                "❌ Nieprawidłowy zakład",
                ephemeral=True
            )
            return

        game = {
            "player": [draw_card(), draw_card()],
            "dealer": [draw_card(), draw_card()],
            "bet": bet
        }

        view = BlackjackView(interaction, game)
        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view
        )
