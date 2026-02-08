import discord
from discord import app_commands
import random
from economy import get_player, save_players

suits = ["♠", "♥", "♦", "♣"]
values = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def draw_card():
    v = random.choice(list(values.keys()))
    s = random.choice(suits)
    return f"{v}{s}"

def hand_value(hand):
    value = sum(values[c[:-1]] for c in hand)
    aces = sum(1 for c in hand if c[:-1] == "A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def hand_text(hand):
    return " ".join(hand)

class BlackjackView(discord.ui.View):
    def __init__(self, interaction, game):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.game = game

    async def interaction_check(self, interaction):
        return interaction.user.id == self.interaction.user.id

    def embed(self, reveal=False, end=False, result=None, color=discord.Color.green()):
    dealer_hand = (
        hand_text(self.game["dealer"])
        if reveal else f"{self.game['dealer'][0]} ❓"
    )

    dealer_value = ""
    if reveal:
        dealer_value = f"**({hand_value(self.game['dealer'])})**"

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


    async def finish(self, interaction):
        dealer = self.game["dealer"]
        p = get_player(interaction.user.id)

        while hand_value(dealer) < 17:
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

        await interaction.response.edit_message(
            embed=self.embed(
                reveal=True,
                end=True,
                result=result,
                color=color
            ),
            view=None
        )

    @discord.ui.button(label="🎴 Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction, button):
        self.game["player"].append(draw_card())
        if hand_value(self.game["player"]) > 21:
            p = get_player(interaction.user.id)
            p["balance"] -= self.game["bet"]
            p["losses"] += 1
            p["games"] += 1
            save_players()
            self.stop()

            await interaction.response.edit_message(
                embed=self.embed(
                    reveal=True,
                    end=True,
                    result="💥 Bust!",
                    color=discord.Color.red()
                ),
                view=None
            )
        else:
            await interaction.response.edit_message(
                embed=self.embed(),
                view=self
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
        self.game["player"].append(draw_card())
        await self.finish(interaction)

def setup(bot):
    @bot.tree.command(name="blackjack", description="Zagraj w BlackJacka")
    @app_commands.describe(bet="Zakład")
    async def blackjack(interaction: discord.Interaction, bet: int):
        p = get_player(interaction.user.id)
        if bet <= 0 or bet > p["balance"]:
            await interaction.response.send_message(
                "❌ Zły zakład",
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
            embed=view.embed(),
            view=view
        )
