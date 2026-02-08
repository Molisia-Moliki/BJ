import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
PLAYER_FILE = "players.json"
START_MONEY = 1000

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- KARTY ----------
cards = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def draw_card():
    return random.choice(list(cards.keys()))

def hand_value(hand):
    value = sum(cards[c] for c in hand)
    aces = hand.count("A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

# ---------- DANE GRACZY ----------
def load_players():
    if not os.path.exists(PLAYER_FILE):
        return {}
    with open(PLAYER_FILE, "r") as f:
        return json.load(f)

def save_players():
    with open(PLAYER_FILE, "w") as f:
        json.dump(players, f, indent=4)

players = load_players()

def get_player(uid):
    uid = str(uid)
    if uid not in players:
        players[uid] = {
            "balance": START_MONEY,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games": 0
        }
        save_players()
    return players[uid]

# ---------- VIEW / BUTTONS ----------
class BlackjackView(discord.ui.View):
    def __init__(self, interaction, game):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.game = game

    async def interaction_check(self, interaction):
        return interaction.user.id == self.interaction.user.id

    def render(self):
        return (
            f"🃏 **BlackJack**\n"
            f"Zakład: {self.game['bet']} 💰\n\n"
            f"Twoje karty: {self.game['player']} "
            f"(= {hand_value(self.game['player'])})\n"
            f"Karta krupiera: {self.game['dealer'][0]}"
        )

    async def finish_game(self, interaction):
        dealer = self.game["dealer"]
        p = get_player(interaction.user.id)

        while hand_value(dealer) < 17:
            dealer.append(draw_card())

        player_value = hand_value(self.game["player"])
        dealer_value = hand_value(dealer)
        bet = self.game["bet"]

        p["games"] += 1

        if dealer_value > 21 or player_value > dealer_value:
            p["balance"] += bet
            p["wins"] += 1
            result = f"🎉 Wygrana +{bet} 💰"
        elif player_value < dealer_value:
            p["balance"] -= bet
            p["losses"] += 1
            result = f"💀 Przegrana -{bet} 💰"
        else:
            p["draws"] += 1
            result = "🤝 Remis"

        save_players()
        self.stop()

        await interaction.response.edit_message(
            content=(
                f"🃏 **Koniec gry**\n"
                f"Ty: {self.game['player']} (= {player_value})\n"
                f"Krupier: {dealer} (= {dealer_value})\n\n"
                f"{result}\n"
                f"Saldo: {p['balance']} 💰"
            ),
            view=None
        )

    # 🎴 HIT
    @discord.ui.button(label="🎴 Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction, button):
        self.game["player"].append(draw_card())
        value = hand_value(self.game["player"])

        if value > 21:
            p = get_player(interaction.user.id)
            p["balance"] -= self.game["bet"]
            p["losses"] += 1
            p["games"] += 1
            save_players()
            self.stop()

            await interaction.response.edit_message(
                content=(
                    f"💥 **Bust!**\n"
                    f"Karty: {self.game['player']} (= {value})\n"
                    f"Strata: {self.game['bet']} 💰\n"
                    f"Saldo: {p['balance']} 💰"
                ),
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=self.render(),
                view=self
            )

    # ✋ STAND
    @discord.ui.button(label="✋ Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction, button):
        await self.finish_game(interaction)

    # 💸 DOUBLE DOWN
    @discord.ui.button(label="💸 Double Down", style=discord.ButtonStyle.blurple)
    async def double_down(self, interaction, button):
        p = get_player(interaction.user.id)

        if p["balance"] < self.game["bet"]:
            await interaction.response.send_message(
                "❌ Brak środków na Double Down.",
                ephemeral=True
            )
            return

        self.game["bet"] *= 2
        self.game["player"].append(draw_card())
        value = hand_value(self.game["player"])

        if value > 21:
            p["balance"] -= self.game["bet"]
            p["losses"] += 1
            p["games"] += 1
            save_players()
            self.stop()

            await interaction.response.edit_message(
                content=(
                    f"💥 **Bust po Double Down!**\n"
                    f"Karty: {self.game['player']} (= {value})\n"
                    f"Strata: {self.game['bet']} 💰\n"
                    f"Saldo: {p['balance']} 💰"
                ),
                view=None
            )
            return

        await self.finish_game(interaction)

# ---------- SLASH COMMANDS ----------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Zalogowano jako {bot.user}")

@bot.tree.command(name="blackjack", description="Zagraj w BlackJacka")
@app_commands.describe(bet="Kwota zakładu")
async def blackjack(interaction: discord.Interaction, bet: int):
    p = get_player(interaction.user.id)

    if bet <= 0 or bet > p["balance"]:
        await interaction.response.send_message(
            "❌ Nieprawidłowy zakład.",
            ephemeral=True
        )
        return

    game = {
        "player": [draw_card(), draw_card()],
        "dealer": [draw_card(), draw_card()],
        "bet": bet
    }

    view = BlackjackView(interaction, game)
    await interaction.response.send_message(view.render(), view=view)

@bot.tree.command(name="stats", description="Twoje statystyki BlackJack")
async def stats(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    await interaction.response.send_message(
        f"📊 **Statystyki {interaction.user.name}**\n"
        f"💰 Saldo: {p['balance']}\n"
        f"🎲 Gry: {p['games']}\n"
        f"🏆 Wygrane: {p['wins']}\n"
        f"💀 Przegrane: {p['losses']}\n"
        f"🤝 Remisy: {p['draws']}",
        ephemeral=True
    )

# ---------- KEEP ALIVE ----------
bot.run(TOKEN)

# Keep alive loop dla Railway
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
