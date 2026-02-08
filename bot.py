import discord
from discord.ext import commands
from economy import get_player
import blackjack
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Zalogowano jako {bot.user}")

# REJESTRACJA MODUŁÓW
blackjack.setup(bot)

bot.run(TOKEN)
