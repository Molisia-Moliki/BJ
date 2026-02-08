import discord
from discord.ext import commands
import random
import json
import os

PLAYER_FILE = "players.json"
START_MONEY = 1000

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

def save_players(players):
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
        save_players(players)
    return players[uid]

# ---------- BLACKJACK GAME CLASS ----------
class BlackjackGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.player = [draw_card(), draw_card()]
        self.dealer = [draw_card(), draw_card()]
        self.finished = False

    def hit(self):
        self.player.append(draw_card())
        value = hand_value(self.player)
        if value > 21:
            self.finished = True
        return value

    def stand(self):
        self.finished = True
        dealer_value = hand_value(self.dealer)
        while dealer_value < 17:
            self.dealer.append(draw_card())
            dealer_value = hand_value(self.dealer)
        return dealer_value

    def double_down(self):
        player_data = get_player(self.user_id)
        if player_data["balance"] < self.bet:
            return False  # brak środków
        self.bet *= 2
        self.player.append(draw_card())
        self.finished = True
        return True

    def result(self):
        p_value = hand_value(self.player)
        d_value = hand_value(self.dealer)
        player_data = get_player(self.user_id)
        player_data["games"] += 1

        if d_value > 21 or p_value > d_value:
            player_data["balance"] += self.bet
            player_data["wins"] += 1
            res = "win"
        elif p_value < d_value:
            player_data["balance"] -= self.bet
            player_data["losses"] += 1
            res = "lose"
        else:
            player_data["draws"] += 1
            res = "draw"

        save_players(players)
        return {
            "result": res,
            "player_hand": self.player,
            "dealer_hand": self.dealer,
            "player_value": p_value,
            "dealer_value": d_value,
            "balance": player_data["balance"]
        }

# ---------- VIEW / BUTTONS (DO DISCORD) ----------
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
            f"Zakład: {self.game.bet} 💰\n\n"
            f"Twoje karty: {self.game.player} "
            f"(= {hand_value(self.game.player)})\n"
            f"Karta krupiera: {self.game.dealer[0]}"
        )

    async def finish_game(self, interaction):
        result = self.game.result()
        self.stop()
        await interaction.response.edit_message(
            content=(
                f"🃏 **Koniec gry**\n"
                f"Ty: {result['player_hand']} (= {result['player_value']})\n"
                f"Krupier: {result['dealer_hand']} (= {result['dealer_value']})\n\n"
                f"Wynik: {result['result'].upper()}\n"
                f"Saldo: {result['balance']} 💰"
            ),
            view=None
        )
