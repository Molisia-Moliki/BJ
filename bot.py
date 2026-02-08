import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import time

# ---------- CONFIG ----------
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

# ---------- DANE ----------
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
            "games": 0,
            "last_daily": 0
        }
        save_players()
    else:
        players[uid].setdefault("last_daily", 0)
    return players[uid]

# ---------- BLACKJACK VIEW ----------
class BlackjackView(discord.ui.View):
    def __init__(self, interaction, game):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.game = game

    async def interaction_check(self, interaction):
        return interaction.user.id == self.interaction.user.id

    def render_embed(self):
        embed = discord.Embed(
            title="🃏 BlackJack",
            description=f"**Zakład:** {self.game['bet']} 💰",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Twoje karty",
            value=f"{self.game['player']} (= {hand_value(self.game['player'])})",
            inline=False
        )
        embed.add_field(
            name="Krupier",
            value=f"{self.game['dealer'][0]} ❓",
            inline=False
        )
        embed.set_footer(text="🎴 Hit | ✋ Stand | 💸 Double Down")
        return embed

    async def finish(self, interaction):
        dealer = self.game["dealer"]
        p = get_player(interaction.user.id)

        while hand_value(dealer) < 17:
            dealer.append(draw_card())

        player_val = hand_value(self.game["player"])
        dealer_val = hand_value(dealer)
        bet = self.game["bet"]

        p["games"] += 1

        # 💥 Bust gracza
        if player_val > 21:
            p["balance"] -= bet
            p["losses"] += 1
            result_text = f"💥 **Bust!** -{bet} 💰"
            color = discord.Color.red()

        # 🎉 Gracz ≤21 i krupier >21
        elif dealer_val > 21:
            p["balance"] += bet
            p["wins"] += 1
            result_text = f"🎉 **Wygrana!** +{bet} 💰"
            color = discord.Color.green()

        # 🔄 Normalne porównanie
        else:
            if player_val > dealer_val:
                p["balance"] += bet
                p["wins"] += 1
                result_text = f"🎉 **Wygrana!** +{bet} 💰"
                color = discord.Color.green()
            elif player_val < dealer_val:
                p["balance"] -= bet
                p["losses"] += 1
                result_text = f"💀 **Przegrana!** -{bet} 💰"
                color = discord.Color.red()
            else:
                p["draws"] += 1
                result_text = "🤝 **Remis**"
                color = discord.Color.orange()

        save_players()
        self.stop()

        embed = discord.Embed(
            title="🃏 BlackJack - Koniec gry",
            color=color
        )
        embed.add_field(name="Twoje karty", value=f"{self.game['player']} (= {player_val})", inline=False)
        embed.add_field(name="Krupier", value=f"{dealer} (= {dealer_val})", inline=False)
        embed.add_field(name="Wynik", value=result_text, inline=False)
        embed.set_footer(text=f"Saldo: {p['balance']} 💰")
        await interaction.response.edit_message(embed=embed, view=None)

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

            embed = discord.Embed(
                title="💥 Bust!",
                description=f"Karty: {self.game['player']} (= {value})\nSaldo: {p['balance']} 💰",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.edit_message(embed=self.render_embed(), view=self)

    @discord.ui.button(label="✋ Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction, button):
        await self.finish(interaction)

    @discord.ui.button(label="💸 Double Down", style=discord.ButtonStyle.blurple)
    async def double(self, interaction, button):
        p = get_player(interaction.user.id)
        if p["balance"] < self.game["bet"]:
            await interaction.response.send_message(
                "❌ Brak środków na Double Down",
                ephemeral=True
            )
            return
        self.game["bet"] *= 2
        self.game["player"].append(draw_card())
        await self.finish(interaction)

# ---------- COMMANDS ----------
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
    await interaction.response.send_message(embed=view.render_embed(), view=view)

@bot.tree.command(name="daily", description="Daily reward 6000 💰 (24h)")
async def daily(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    now = int(time.time())
    cooldown = 24 * 60 * 60

    remaining = cooldown - (now - p.get("last_daily", 0))
    if remaining > 0:
        h = remaining // 3600
        m = (remaining % 3600) // 60
        embed = discord.Embed(
            title="⏳ Daily już odebrane!",
            description=f"Spróbuj ponownie za **{h}h {m}m**",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    p["balance"] += 6000
    p["last_daily"] = now
    save_players()

    embed = discord.Embed(
        title="🎁 Daily Reward!",
        description=f"+6000 💰\nSaldo: {p['balance']} 💰",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="Twoje statystyki")
async def stats(interaction: discord.Interaction):
    p = get_player(interaction.user.id)
    embed = discord.Embed(
        title=f"📊 Statystyki {interaction.user.name}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="💰 Saldo", value=p["balance"], inline=True)
    embed.add_field(name="🎲 Gry", value=p["games"], inline=True)
    embed.add_field(name="🏆 Wygrane", value=p["wins"], inline=True)
    embed.add_field(name="💀 Przegrane", value=p["losses"], inline=True)
    embed.add_field(name="🤝 Remisy", value=p["draws"], inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)
