import json
import os
import time

PLAYER_FILE = "players.json"
START_MONEY = 1000

def load_players():
    if not os.path.exists(PLAYER_FILE):
        return {}
    with open(PLAYER_FILE, "r") as f:
        return json.load(f)

players = load_players()

def save_players():
    with open(PLAYER_FILE, "w") as f:
        json.dump(players, f, indent=4)

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

async def daily_reward(interaction):
    p = get_player(interaction.user.id)
    now = int(time.time())
    cooldown = 24 * 60 * 60

    remaining = cooldown - (now - p["last_daily"])
    if remaining > 0:
        h = remaining // 3600
        m = (remaining % 3600) // 60
        await interaction.response.send_message(
            f"⏳ Daily za {h}h {m}m",
            ephemeral=True
        )
        return

    p["balance"] += 6000
    p["last_daily"] = now
    save_players()

    await interaction.response.send_message(
        f"🎁 **DAILY!** +6000 💰\nSaldo: {p['balance']} 💰"
    )
