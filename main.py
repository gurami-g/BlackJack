import array
import json
import os
import random
import pygame

# Pygame და Mixer ინიციალიზაცია
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1)

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack - Fixed Split Hand Turn Management")
clock = pygame.time.Clock()

SAVE_FILE = "save_data.json"


# 🔊 ხმოვანი ეფექტების გენერატორი
def generate_sound(wave_type="chip"):
    sample_rate = 44100
    if wave_type == "chip":
        duration = 0.05
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            v = int(
                32767
                * (0.5 * random.uniform(-1, 1))
                * (1 - i / samples)
            )
            buf.append(v)
        return pygame.mixer.Sound(buffer=buf)

    elif wave_type == "card":
        duration = 0.08
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            v = int(
                32767
                * (0.8 * random.uniform(-0.5, 0.5))
                * (1 - i / samples)
            )
            buf.append(v)
        return pygame.mixer.Sound(buffer=buf)

    elif wave_type == "win":
        duration = 0.3
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            freq = 440 if i < samples / 2 else 660
            t = float(i) / sample_rate
            v = int(
                16000
                * (1 - i / samples)
                * (1 if (t * freq * 2) % 2 > 1 else -1)
            )
            buf.append(v)
        return pygame.mixer.Sound(buffer=buf)

    elif wave_type == "lose":
        duration = 0.3
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            t = float(i) / sample_rate
            freq = 200 - (100 * (i / samples))
            v = int(
                16000
                * (1 - i / samples)
                * (1 if (t * freq * 2) % 2 > 1 else -1)
            )
            buf.append(v)
        return pygame.mixer.Sound(buffer=buf)


SOUND_CHIP = generate_sound("chip")
SOUND_CARD = generate_sound("card")
SOUND_WIN = generate_sound("win")
SOUND_LOSE = generate_sound("lose")

# 🎨 ფერები
BG_DARK_GREEN = (12, 50, 25)
BG_LIGHT_GREEN = (22, 80, 40)
GOLD = (240, 195, 50)
GOLD_BORDER = (180, 140, 30)
WHITE = (250, 250, 250)
BLACK = (20, 20, 20)
RED_SUIT = (210, 30, 30)
DARK_GRAY = (45, 50, 55)
DISABLED_GRAY = (30, 33, 36)
HOVER_GRAY = (75, 80, 85)
RED_BTN = (180, 40, 40)
HOVER_RED = (220, 60, 60)
PURPLE_BTN = (120, 40, 140)
HOVER_PURPLE = (160, 60, 180)
BLUE_BTN = (30, 100, 160)
HOVER_BLUE = (50, 130, 200)
SHADOW = (10, 30, 15)

# შრიფტები
FONT_TITLE = pygame.font.SysFont("Segoe UI", 42, bold=True)
FONT_LARGE = pygame.font.SysFont("Segoe UI", 28, bold=True)
FONT_MEDIUM = pygame.font.SysFont("Segoe UI", 16, bold=True)
FONT_BTN = pygame.font.SysFont("Segoe UI", 14, bold=True)
FONT_SMALL = pygame.font.SysFont("Segoe UI", 13, bold=True)

VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]

BOT_PROFILES = [
    {"name": "ლაშა (ფრთხილი)", "style": "cautious"},
    {"name": "გიორგი (აგრესიული)", "style": "aggressive"},
    {"name": "ნინო (პრო)", "style": "pro"},
]


def create_shoe(num_decks=6):
    deck = []
    for _ in range(num_decks):
        for suit in SUITS:
            for val in VALUES:
                deck.append({"value": val, "suit": suit})
    random.shuffle(deck)
    return deck


def get_card_value(card):
    val = card["value"]
    if val in ["J", "Q", "K"]:
        return 10
    if val == "A":
        return 11
    return int(val)


def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        val = get_card_value(card)
        score += val
        if card["value"] == "A":
            aces += 1
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score


class Button:

    def __init__(self, x, y, w, h, text, color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.enabled = True

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()

        if not self.enabled:
            current_color = DISABLED_GRAY
            border_col = DARK_GRAY
            text_col = (120, 120, 120)
        else:
            current_color = (
                self.hover_color
                if self.rect.collidepoint(mouse_pos)
                else self.color
            )
            border_col = GOLD
            text_col = WHITE

        pygame.draw.rect(
            surface, SHADOW, self.rect.move(2, 3), border_radius=10
        )
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=10)

        text_surf = FONT_BTN.render(self.text, True, text_col)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if self.rect.collidepoint(event.pos):
                return True
        return False


class ChipButton:

    def __init__(self, x, y, radius, value, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.value = value
        self.color = color

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        dist = (
            (mouse_pos[0] - self.x) ** 2 + (mouse_pos[1] - self.y) ** 2
        ) ** 0.5
        is_hover = dist <= self.radius

        pygame.draw.circle(
            surface, SHADOW, (self.x + 2, self.y + 3), self.radius
        )
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
        border_col = WHITE if is_hover else GOLD
        pygame.draw.circle(
            surface, border_col, (self.x, self.y), self.radius, 3
        )
        pygame.draw.circle(
            surface, WHITE, (self.x, self.y), self.radius - 6, 1
        )

        text_surf = FONT_SMALL.render(f"${self.value}", True, WHITE)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dist = (
                (event.pos[0] - self.x) ** 2 + (event.pos[1] - self.y) ** 2
            ) ** 0.5
            return dist <= self.radius
        return False


def draw_card(surface, x, y, card, hidden=False):
    rect = pygame.Rect(x, y, 65, 95)
    pygame.draw.rect(surface, SHADOW, rect.move(2, 3), border_radius=6)

    if hidden:
        pygame.draw.rect(surface, RED_BTN, rect, border_radius=6)
        pygame.draw.rect(surface, GOLD, rect, 2, border_radius=6)
        pygame.draw.rect(
            surface, WHITE, (x + 6, y + 6, 53, 83), 1, border_radius=4
        )
    else:
        pygame.draw.rect(surface, WHITE, rect, border_radius=6)
        pygame.draw.rect(surface, GOLD_BORDER, rect, 2, border_radius=6)

        suit = card["suit"]
        val_str = str(card["value"])
        color = RED_SUIT if suit in ["♥", "♦"] else BLACK

        val_surf = FONT_MEDIUM.render(val_str, True, color)
        surface.blit(val_surf, (x + 5, y + 3))

        suit_surf = FONT_LARGE.render(suit, True, color)
        suit_rect = suit_surf.get_rect(center=(x + 32, y + 48))
        surface.blit(suit_surf, suit_rect)


# ---------------------------------------------------------
# თამაშის მთავარი კლასი
# ---------------------------------------------------------
class ProCasinoBlackjack:

    def __init__(self):
        self.app_state = "MAIN_MENU"
        self.player_count = 1

        self.wins = 0
        self.losses = 0
        self.draws = 0

        self.xp = 0
        self.level = 1
        self.player_balance = 1000

        self.shoe = create_shoe(6)
        self.running_count = 0

        self.hint_text = ""
        self.insurance_taken = False
        self.insurance_amount = 0

        self.side_bet_pairs = 0
        self.side_bet_21_3 = 0

        self.load_game_data()

        self.btn_play_ai = Button(
            350, 260, 300, 55, "კომპიუტერთან თამაში", DARK_GRAY, HOVER_GRAY
        )
        self.btn_play_friends = Button(
            350, 340, 300, 55, "მეგობრებთან თამაში", PURPLE_BTN, HOVER_PURPLE
        )

        self.btn_p1 = Button(
            300, 300, 80, 50, "1", DARK_GRAY, HOVER_GRAY
        )
        self.btn_p2 = Button(
            400, 300, 80, 50, "2", DARK_GRAY, HOVER_GRAY
        )
        self.btn_p3 = Button(
            500, 300, 80, 50, "3", DARK_GRAY, HOVER_GRAY
        )
        self.btn_p4 = Button(
            600, 300, 80, 50, "4", DARK_GRAY, HOVER_GRAY
        )
        self.btn_back_to_main = Button(
            380, 420, 240, 45, "უკან დაბრუნება", RED_BTN, HOVER_RED
        )

        self.btn_menu = Button(
            25, 20, 110, 38, "მენიუ", RED_BTN, HOVER_RED
        )

        self.reset_game()

    def save_game_data(self):
        data = {
            "balance": self.players[0]["balance"]
            if hasattr(self, "players")
            else self.player_balance,
            "xp": self.xp,
            "level": self.level,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_game_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.player_balance = data.get("balance", 1000)
                    self.xp = data.get("xp", 0)
                    self.level = data.get("level", 1)
                    self.wins = data.get("wins", 0)
                    self.losses = data.get("losses", 0)
                    self.draws = data.get("draws", 0)
            except:
                self.player_balance = 1000

    def update_card_count(self, card):
        v = card["value"]
        if v in [2, 3, 4, 5, 6]:
            self.running_count += 1
        elif v in [10, "J", "Q", "K", "A"]:
            self.running_count -= 1

    def draw_card_from_shoe(self):
        if len(self.shoe) < 50:
            self.shoe = create_shoe(6)
            self.running_count = 0
            self.message = "ბანქოს დასტა აირია! (Reshuffled)"

        card = self.shoe.pop()
        self.update_card_count(card)
        return card

    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.level * 100:
            self.level += 1

    def reset_game(self):
        self.bet = 0
        self.side_bet_pairs = 0
        self.side_bet_21_3 = 0
        self.state = "BETTING"
        self.message = "აირჩიეთ ჩიპები და დააჭირეთ 'დარიგებას'!"
        self.hint_text = ""
        self.insurance_taken = False
        self.insurance_amount = 0

        self.dealer_hand = []

        self.players = []
        for i in range(getattr(self, "player_count", 1)):
            if i == 0:
                name = "თქვენ"
                style = "human"
                bal = getattr(self, "player_balance", 1000)
            else:
                profile = BOT_PROFILES[(i - 1) % len(BOT_PROFILES)]
                name = profile["name"]
                style = profile["style"]
                bal = 1000

            self.players.append(
                {
                    "name": name,
                    "style": style,
                    "is_bot": i > 0,
                    "balance": bal if bal > 0 else 1000,
                    "bet": 0,
                    "hand": [],
                    "done": False,
                }
            )

        self.active_player_index = 0

        self.chips = [
            ChipButton(180, 600, 22, 10, (200, 50, 50)),
            ChipButton(235, 600, 22, 50, (50, 100, 200)),
            ChipButton(290, 600, 22, 100, (40, 40, 40)),
            ChipButton(345, 600, 22, 500, (180, 150, 30)),
        ]

        self.btn_hint = Button(
            840, 20, 120, 38, "რჩევა (AI)", BLUE_BTN, HOVER_BLUE
        )
        self.btn_all_in = Button(
            390, 580, 100, 42, "ALL-IN", PURPLE_BTN, HOVER_PURPLE
        )
        self.btn_clear_bet = Button(
            500, 580, 110, 42, "გასუფთავება", DARK_GRAY, HOVER_GRAY
        )
        self.btn_deal = Button(
            620, 580, 110, 42, "დარიგება", RED_BTN, HOVER_RED
        )

        self.btn_hit = Button(
            40, 580, 100, 42, "ბანქო", DARK_GRAY, HOVER_GRAY
        )
        self.btn_stand = Button(
            150, 580, 100, 42, "გაჩერება", DARK_GRAY, HOVER_GRAY
        )
        self.btn_double = Button(
            260, 580, 110, 42, "გაორმაგება", DARK_GRAY, HOVER_GRAY
        )
        self.btn_split = Button(
            380, 580, 100, 42, "გაყოფა", DARK_GRAY, HOVER_GRAY
        )
        self.btn_surrender = Button(
            490, 580, 100, 42, "დათმობა", DARK_GRAY, HOVER_GRAY
        )
        self.btn_insurance = Button(
            600, 580, 110, 42, "დაზღვევა", GOLD_BORDER, GOLD
        )

        self.btn_restart = Button(
            400, 580, 200, 45, "დაიწყე თავიდან", RED_BTN, HOVER_RED
        )

    def start_game_with_players(self, num_players):
        self.player_count = num_players
        self.app_state = "GAME"
        self.reset_game()

    def all_in(self):
        p0 = self.players[0]
        if p0["balance"] > 0:
            self.bet = p0["balance"]
            SOUND_CHIP.play()

    def evaluate_side_bets(self):
        p0 = self.players[0]
        h = p0["hand"]
        d_up = self.dealer_hand[0]

        side_msg = []

        if self.side_bet_pairs > 0 and len(h) == 2:
            if h[0]["value"] == h[1]["value"]:
                win_amount = self.side_bet_pairs * 25
                p0["balance"] += win_amount
                side_msg.append(f"Pairs (+${win_amount})")
            else:
                side_msg.append("Pairs წაგება")

        if self.side_bet_21_3 > 0 and len(h) == 2:
            three_cards = [h[0], h[1], d_up]
            suits = [c["suit"] for c in three_cards]
            vals = [get_card_value(c) for c in three_cards]

            is_flush = len(set(suits)) == 1
            is_three_kind = len(set(vals)) == 1

            if is_flush or is_three_kind:
                win_amount = self.side_bet_21_3 * 9
                p0["balance"] += win_amount
                side_msg.append(f"21+3 (+${win_amount})")
            else:
                side_msg.append("21+3 წაგება")

        if side_msg:
            self.message = " | ".join(side_msg)
        else:
            self.message = "თქვენი სვლაა!"

    def start_new_round(self):
        p0 = self.players[0]
        total_req = self.bet + self.side_bet_pairs + self.side_bet_21_3

        if self.bet <= 0:
            self.message = "გთხოვთ, დადოთ ფსონი!"
            return
        if p0["balance"] < total_req:
            self.message = "არ გაქვთ საკმარისი ბალანსი!"
            return

        SOUND_CARD.play()
        self.hint_text = ""
        self.insurance_taken = False
        self.insurance_amount = 0

        p0["balance"] -= total_req

        for p in self.players:
            if p["is_bot"]:
                if p["style"] == "cautious":
                    bot_bet = min(
                        p["balance"], max(10, (p["balance"] // 30) // 10 * 10)
                    )
                elif p["style"] == "aggressive":
                    bot_bet = min(
                        p["balance"], max(50, (p["balance"] // 5) // 10 * 10)
                    )
                else:
                    bot_bet = min(
                        p["balance"], max(25, (p["balance"] // 15) // 10 * 10)
                    )

                p["bet"] = bot_bet
                p["balance"] -= p["bet"]
            else:
                p["bet"] = self.bet

            p["hand"] = [
                self.draw_card_from_shoe(),
                self.draw_card_from_shoe(),
            ]
            p["done"] = False

        self.dealer_hand = [
            self.draw_card_from_shoe(),
            self.draw_card_from_shoe(),
        ]
        self.active_player_index = 0

        self.evaluate_side_bets()

        self.state = "PLAYING"

    def take_insurance(self):
        if (
            self.state == "PLAYING"
            and not self.insurance_taken
            and not self.players[self.active_player_index]["is_bot"]
        ):
            curr = self.players[self.active_player_index]
            cost = curr["bet"] // 2

            if cost > 0 and self.players[0]["balance"] >= cost:
                SOUND_CHIP.play()
                self.players[0]["balance"] -= cost
                self.insurance_taken = True
                self.insurance_amount = cost
                self.message = f"დაზღვევა იყიდეთ (+${cost})!"

    def get_ai_hint(self):
        if (
            self.state != "PLAYING"
            or self.players[self.active_player_index]["is_bot"]
        ):
            return

        curr = self.players[self.active_player_index]
        p_score = calculate_score(curr["hand"])
        d_up = get_card_value(self.dealer_hand[0])

        if (
            len(curr["hand"]) == 2
            and get_card_value(curr["hand"][0]) == get_card_value(curr["hand"][1])
        ):
            self.hint_text = "AI რჩევა: გაყავით ხელი (Split)"
        elif p_score >= 17:
            self.hint_text = "AI რჩევა: გაჩერდით (Stand)"
        elif p_score <= 11:
            if p_score in [10, 11] and len(curr["hand"]) == 2:
                self.hint_text = "AI რჩევა: გააორმაგეთ (Double)"
            else:
                self.hint_text = "AI რჩევა: აიღეთ ბანქო (Hit)"
        elif 12 <= p_score <= 16:
            if d_up >= 7:
                self.hint_text = "AI რჩევა: აიღეთ ბანქო (Hit)"
            else:
                self.hint_text = "AI რჩევა: გაჩერდით (Stand)"

    def is_human_turn(self):
        return (
            self.state == "PLAYING"
            and self.active_player_index < len(self.players)
            and not self.players[self.active_player_index]["is_bot"]
        )

    def hit(self):
        if not self.is_human_turn():
            return
        SOUND_CARD.play()
        self.hint_text = ""
        curr = self.players[self.active_player_index]
        curr["hand"].append(self.draw_card_from_shoe())

        if calculate_score(curr["hand"]) >= 21:
            self.next_turn()

    def stand(self):
        if not self.is_human_turn():
            return
        self.hint_text = ""
        self.next_turn()

    def double_down(self):
        if not self.is_human_turn():
            return
        self.hint_text = ""
        curr = self.players[self.active_player_index]
        p0 = self.players[0]

        if len(curr["hand"]) == 2 and p0["balance"] >= curr["bet"]:
            SOUND_CHIP.play()
            SOUND_CARD.play()
            p0["balance"] -= curr["bet"]
            curr["bet"] *= 2
            curr["hand"].append(self.draw_card_from_shoe())
            self.next_turn()

    def split(self):
        if not self.is_human_turn():
            return

        curr = self.players[self.active_player_index]
        hand = curr["hand"]
        p0 = self.players[0]

        can_split = (len(hand) == 2) and (
            get_card_value(hand[0]) == get_card_value(hand[1])
        )

        if can_split and p0["balance"] >= curr["bet"]:
            SOUND_CHIP.play()
            SOUND_CARD.play()
            p0["balance"] -= curr["bet"]

            hand1 = [hand[0], self.draw_card_from_shoe()]
            hand2 = [hand[1], self.draw_card_from_shoe()]

            curr["hand"] = hand1

            # ✂️ ახალი ხელის ჩასმა უშუალოდ მიმდინარე ხელის შემდეგ
            self.players.insert(
                self.active_player_index + 1,
                {
                    "name": f"{curr['name']} (ხელი 2)",
                    "style": "human",
                    "is_bot": False,
                    "balance": 0,
                    "bet": curr["bet"],
                    "hand": hand2,
                    "done": False,
                },
            )
            self.message = "ხელი გაიყო ორად!"

    def surrender(self):
        if self.is_human_turn():
            curr = self.players[self.active_player_index]
            p0 = self.players[0]
            if len(curr["hand"]) == 2:
                refund = curr["bet"] // 2
                p0["balance"] += refund
                self.losses += 1
                self.message = f"დათმეთ ხელი! დაგიბრუნდათ ${refund}"
                self.next_turn()
                SOUND_LOSE.play()

    def play_bot_turns(self):
        d_up = get_card_value(self.dealer_hand[0])

        while (
            self.active_player_index < len(self.players)
            and self.players[self.active_player_index]["is_bot"]
        ):
            bot = self.players[self.active_player_index]
            style = bot["style"]

            if (
                style == "aggressive"
                and len(bot["hand"]) == 2
                and bot["balance"] >= bot["bet"]
            ):
                b_score = calculate_score(bot["hand"])
                if b_score in [9, 10, 11]:
                    bot["balance"] -= bot["bet"]
                    bot["bet"] *= 2
                    bot["hand"].append(self.draw_card_from_shoe())
                    bot["done"] = True
                    self.active_player_index += 1
                    continue

            while calculate_score(bot["hand"]) < 21:
                b_score = calculate_score(bot["hand"])

                if style == "cautious":
                    if b_score >= 15:
                        break
                    elif b_score >= 12 and d_up <= 6:
                        break
                    else:
                        bot["hand"].append(self.draw_card_from_shoe())

                elif style == "aggressive":
                    if b_score >= 17:
                        break
                    else:
                        bot["hand"].append(self.draw_card_from_shoe())

                else:
                    if b_score >= 17:
                        break
                    elif b_score <= 11:
                        bot["hand"].append(self.draw_card_from_shoe())
                    elif 12 <= b_score <= 16:
                        if d_up >= 7:
                            bot["hand"].append(self.draw_card_from_shoe())
                        else:
                            break

            bot["done"] = True
            self.active_player_index += 1

        if self.active_player_index >= len(self.players):
            self.end_round()

    def next_turn(self):
        if self.active_player_index < len(self.players):
            self.players[self.active_player_index]["done"] = True

        self.active_player_index += 1

        if self.active_player_index >= len(self.players):
            self.end_round()
        elif self.players[self.active_player_index]["is_bot"]:
            self.play_bot_turns()

    def end_round(self):
        any_valid = any(
            calculate_score(p["hand"]) <= 21 for p in self.players
        )
        if any_valid:
            while calculate_score(self.dealer_hand) < 17:
                self.dealer_hand.append(self.draw_card_from_shoe())

        d_score = calculate_score(self.dealer_hand)
        d_has_bj = (
            len(self.dealer_hand) == 2
            and calculate_score(self.dealer_hand) == 21
        )

        if self.insurance_taken and d_has_bj:
            ins_payout = self.insurance_amount * 3
            self.players[0]["balance"] += ins_payout

        summary = []
        self.add_xp(25)

        for idx, p in enumerate(self.players, 1):
            p_score = calculate_score(p["hand"])
            b = p["bet"]
            is_bj = len(p["hand"]) == 2 and p_score == 21

            if p_score > 21:
                summary.append(f"{p['name']}: წააგო")
                if not p["is_bot"]:
                    self.losses += 1
            elif d_score > 21 or p_score > d_score:
                payout = int(b * 2.5) if (is_bj and not d_has_bj) else b * 2
                if not p["is_bot"]:
                    self.players[0]["balance"] += payout
                else:
                    p["balance"] += payout

                win_val = int(b * 1.5) if (is_bj and not d_has_bj) else b
                summary.append(f"{p['name']}: მოიგო (+${win_val})")

                if not p["is_bot"]:
                    self.wins += 1
                    self.add_xp(50)
            elif p_score < d_score:
                summary.append(f"{p['name']}: წააგო")
                if not p["is_bot"]:
                    self.losses += 1
            else:
                if not p["is_bot"]:
                    self.players[0]["balance"] += b
                else:
                    p["balance"] += b
                summary.append(f"{p['name']}: ფრე")
                if not p["is_bot"]:
                    self.draws += 1

        p0_win = calculate_score(self.players[0]["hand"]) <= 21 and (
            d_score > 21
            or calculate_score(self.players[0]["hand"]) > d_score
        )
        if p0_win or (self.insurance_taken and d_has_bj):
            SOUND_WIN.play()
        else:
            SOUND_LOSE.play()

        self.message = " | ".join(summary)

        self.player_balance = self.players[0]["balance"]
        self.save_game_data()

        if self.players[0]["balance"] <= 0:
            self.state = "BANKRUPT"
            self.message = "თქვენ გაკოტრდით!"
        else:
            self.state = "GAME_OVER"

    def draw(self, surface):
        surface.fill(BG_DARK_GREEN)
        pygame.draw.circle(
            surface, BG_LIGHT_GREEN, (WIDTH // 2, HEIGHT // 2 - 40), 420
        )

        pygame.draw.rect(
            surface,
            GOLD_BORDER,
            (15, 15, WIDTH - 30, HEIGHT - 30),
            3,
            border_radius=15,
        )

        if self.app_state == "MAIN_MENU":
            title = FONT_TITLE.render("BLACKJACK CASINO", True, GOLD)
            title_rect = title.get_rect(center=(WIDTH // 2, 160))
            surface.blit(title, title_rect)

            self.btn_play_ai.draw(surface)
            self.btn_play_friends.draw(surface)

        elif self.app_state == "PLAYER_SELECT":
            title = FONT_TITLE.render(
                "აირჩიეთ მოთამაშეთა რაოდენობა", True, GOLD
            )
            title_rect = title.get_rect(center=(WIDTH // 2, 180))
            surface.blit(title, title_rect)

            self.btn_p1.draw(surface)
            self.btn_p2.draw(surface)
            self.btn_p3.draw(surface)
            self.btn_p4.draw(surface)
            self.btn_back_to_main.draw(surface)

        elif self.app_state == "MULTIPLAYER_MENU":
            title = FONT_TITLE.render("ონლაინ რეჟიმი", True, GOLD)
            title_rect = title.get_rect(center=(WIDTH // 2, 180))
            surface.blit(title, title_rect)

            info = FONT_MEDIUM.render(
                "სერვერთან კავშირის დასამყარებლად გაშვით server.py",
                True,
                WHITE,
            )
            info_rect = info.get_rect(center=(WIDTH // 2, 280))
            surface.blit(info, info_rect)

            self.btn_back_to_main.draw(surface)

        elif self.app_state == "GAME":
            self.btn_menu.draw(surface)

            p0 = self.players[0]

            stats_txt = (
                f"ბალანსი: ${p0['balance']}  |  ფსონი: ${self.bet}  |  "
                f"Count: {self.running_count}  |  დონე: {self.level}"
            )
            info_surf = FONT_SMALL.render(stats_txt, True, GOLD)
            surface.blit(info_surf, (150, 25))

            self.btn_hint.enabled = self.is_human_turn()
            self.btn_hint.draw(surface)

            if self.hint_text:
                hint_surf = FONT_MEDIUM.render(self.hint_text, True, GOLD)
                hint_rect = hint_surf.get_rect(
                    center=(WIDTH // 2, HEIGHT - 135)
                )
                surface.blit(hint_surf, hint_rect)

            msg_surf = FONT_MEDIUM.render(self.message, True, WHITE)
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - 165))
            surface.blit(msg_surf, msg_rect)

            dealer_lbl = FONT_MEDIUM.render("დილერის ხელი", True, GOLD)
            surface.blit(dealer_lbl, (50, 65))

            for idx, card in enumerate(self.dealer_hand):
                hidden = idx == 1 and self.state == "PLAYING"
                draw_card(surface, 50 + idx * 75, 95, card, hidden)

            if self.state != "PLAYING" and self.dealer_hand:
                d_score = calculate_score(self.dealer_hand)
                d_score_txt = FONT_SMALL.render(
                    f"ქულა: {d_score}", True, WHITE
                )
                surface.blit(d_score_txt, (50, 200))

            num_players = len(self.players)
            spacing = (
                200 if num_players >= 4 else (230 if num_players == 3 else 280)
            )
            card_offset = 25 if num_players >= 4 else 35
            start_y = 275

            for h_idx, p in enumerate(self.players):
                start_x = 50 + h_idx * spacing

                if self.state == "PLAYING" and h_idx == self.active_player_index:
                    box_width = 100 + (len(p["hand"]) - 1) * card_offset
                    pygame.draw.rect(
                        surface,
                        GOLD,
                        (start_x - 6, start_y - 6, box_width, 135),
                        2,
                        border_radius=10,
                    )

                for c_idx, card in enumerate(p["hand"]):
                    draw_card(
                        surface, start_x + c_idx * card_offset, start_y, card
                    )

                p_score = calculate_score(p["hand"])
                bal_disp = (
                    p0["balance"] if not p["is_bot"] else p["balance"]
                )
                hand_info = (
                    f"{p['name']} ({p_score}) | ${bal_disp}"
                    if self.state != "BETTING"
                    else f"{p['name']} | ${bal_disp}"
                )
                p_score_txt = FONT_SMALL.render(hand_info, True, WHITE)
                surface.blit(p_score_txt, (start_x, start_y + 105))

            if self.state in ["BETTING", "GAME_OVER"]:
                for chip in self.chips:
                    chip.draw(surface)
                self.btn_all_in.draw(surface)
                self.btn_clear_bet.draw(surface)
                self.btn_deal.draw(surface)

                pairs_btn_txt = (
                    f"Pairs (${self.side_bet_pairs})"
                    if self.side_bet_pairs > 0
                    else "Pairs (+10)"
                )
                b21_3_btn_txt = (
                    f"21+3 (${self.side_bet_21_3})"
                    if self.side_bet_21_3 > 0
                    else "21+3 (+10)"
                )

                btn_pairs = Button(
                    750, 520, 110, 35, pairs_btn_txt, BLUE_BTN, HOVER_BLUE
                )
                btn_21_3 = Button(
                    870, 520, 110, 35, b21_3_btn_txt, BLUE_BTN, HOVER_BLUE
                )

                btn_pairs.draw(surface)
                btn_21_3.draw(surface)

                self.btn_side_pairs_inst = btn_pairs
                self.btn_side_21_3_inst = btn_21_3

            elif self.state == "PLAYING":
                is_human = self.is_human_turn()
                curr = (
                    self.players[self.active_player_index]
                    if is_human
                    else self.players[0]
                )

                can_double = (
                    is_human
                    and len(curr["hand"]) == 2
                    and p0["balance"] >= curr["bet"]
                )
                can_split = (
                    is_human
                    and len(curr["hand"]) == 2
                    and get_card_value(curr["hand"][0])
                    == get_card_value(curr["hand"][1])
                    and p0["balance"] >= curr["bet"]
                )
                can_surrender = is_human and len(curr["hand"]) == 2
                can_insure = (
                    is_human
                    and self.dealer_hand
                    and self.dealer_hand[0]["value"] == "A"
                    and not self.insurance_taken
                    and p0["balance"] >= (curr["bet"] // 2)
                )

                self.btn_hit.enabled = is_human
                self.btn_stand.enabled = is_human
                self.btn_double.enabled = can_double
                self.btn_split.enabled = can_split
                self.btn_surrender.enabled = can_surrender
                self.btn_insurance.enabled = can_insure

                self.btn_hit.draw(surface)
                self.btn_stand.draw(surface)
                self.btn_double.draw(surface)
                self.btn_split.draw(surface)
                self.btn_surrender.draw(surface)

                if can_insure:
                    self.btn_insurance.draw(surface)

            elif self.state == "BANKRUPT":
                self.btn_restart.draw(surface)


def main():
    game = ProCasinoBlackjack()
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.save_game_data()
                running = False

            if game.app_state == "MAIN_MENU":
                if game.btn_play_ai.is_clicked(event):
                    game.app_state = "PLAYER_SELECT"
                elif game.btn_play_friends.is_clicked(event):
                    game.app_state = "MULTIPLAYER_MENU"

            elif game.app_state == "PLAYER_SELECT":
                if game.btn_p1.is_clicked(event):
                    game.start_game_with_players(1)
                elif game.btn_p2.is_clicked(event):
                    game.start_game_with_players(2)
                elif game.btn_p3.is_clicked(event):
                    game.start_game_with_players(3)
                elif game.btn_p4.is_clicked(event):
                    game.start_game_with_players(4)
                elif game.btn_back_to_main.is_clicked(event):
                    game.app_state = "MAIN_MENU"

            elif game.app_state == "MULTIPLAYER_MENU":
                if game.btn_back_to_main.is_clicked(event):
                    game.app_state = "MAIN_MENU"

            elif game.app_state == "GAME":
                if game.btn_menu.is_clicked(event):
                    game.save_game_data()
                    game.app_state = "MAIN_MENU"

                if game.btn_hint.is_clicked(event):
                    game.get_ai_hint()

                if game.state in ["BETTING", "GAME_OVER"]:
                    p0 = game.players[0]
                    for chip in game.chips:
                        if chip.is_clicked(event):
                            if p0["balance"] >= game.bet + chip.value:
                                SOUND_CHIP.play()
                                game.bet += chip.value

                    if (
                        hasattr(game, "btn_side_pairs_inst")
                        and game.btn_side_pairs_inst.is_clicked(event)
                    ):
                        if p0["balance"] >= game.bet + game.side_bet_pairs + 10:
                            SOUND_CHIP.play()
                            game.side_bet_pairs += 10

                    elif (
                        hasattr(game, "btn_side_21_3_inst")
                        and game.btn_side_21_3_inst.is_clicked(event)
                    ):
                        if p0["balance"] >= game.bet + game.side_bet_21_3 + 10:
                            SOUND_CHIP.play()
                            game.side_bet_21_3 += 10

                    if game.btn_all_in.is_clicked(event):
                        game.all_in()
                    elif game.btn_clear_bet.is_clicked(event):
                        game.bet = 0
                        game.side_bet_pairs = 0
                        game.side_bet_21_3 = 0
                    elif game.btn_deal.is_clicked(event):
                        game.start_new_round()

                elif game.state == "PLAYING":
                    if game.btn_hit.is_clicked(event):
                        game.hit()
                    elif game.btn_stand.is_clicked(event):
                        game.stand()
                    elif game.btn_double.is_clicked(event):
                        game.double_down()
                    elif game.btn_split.is_clicked(event):
                        game.split()
                    elif game.btn_surrender.is_clicked(event):
                        game.surrender()
                    elif game.btn_insurance.is_clicked(event):
                        game.take_insurance()

                elif game.state == "BANKRUPT":
                    if game.btn_restart.is_clicked(event):
                        game.reset_game()

        game.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()