import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Importujemy gry
import blackjack
import anime_cards

# Przekazujemy bota do modułów gier
blackjack.setup(bot)
anime_cards.setup(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online jako {bot.user}")

bot.run(TOKEN)

# Keep alive loop dla Railway
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
