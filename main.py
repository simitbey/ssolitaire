import curses
import os
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set
from enum import Enum
import sys
import pyfiglet
import pygame

MAIN_FIGLET_FONT = 'larry3d'
PYFIGLET_FONT = 'slant'


class SoundEffects:
    def __init__(self):
        # First, try to quit any existing pygame instance
        try:
            pygame.mixer.quit()
            pygame.quit()
        except:
            pass

        # Wait a moment to ensure cleanup
        import time
        time.sleep(0.1)

        # Initialize pygame itself first
        pygame.init()

        # Initialize pygame mixer with good audio quality
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"Warning: Could not initialize sound system: {e}")
            self.sound_enabled = False
            return

        self.sound_enabled = True

        # Create channel for effects
        pygame.mixer.set_num_channels(1)
        self.effect_channel = pygame.mixer.Channel(0)

        # Define sound file paths relative to main.py
        sound_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
        self.soundtrack_path = os.path.join(sound_dir, 'soundtrack.wav')

        # Load sound effects
        try:
            self.card_flip = self._load_sound(os.path.join(sound_dir, 'card_flip.wav'))
            self.card_place = self._load_sound(os.path.join(sound_dir, 'card_place.wav'))
            self.foundation_complete = self._load_sound(os.path.join(sound_dir, 'foundation_complete.wav'))
            self.game_win = self._load_sound(os.path.join(sound_dir, 'game_win.wav'))
            self.game_over = self._load_sound(os.path.join(sound_dir, 'game_over.wav'))
            self.error = self._load_sound(os.path.join(sound_dir, 'error.wav'))

            # Set volumes
            if self.card_flip: self.card_flip.set_volume(0.3)
            if self.card_place: self.card_place.set_volume(0.3)
            if self.foundation_complete: self.foundation_complete.set_volume(0.4)
            if self.game_win: self.game_win.set_volume(0.4)
            if self.game_over: self.game_over.set_volume(0.4)
            if self.error: self.error.set_volume(0.2)

        except Exception as e:
            print(f"Warning: Could not load sound files: {e}")
            self.sound_enabled = False

    def _load_sound(self, path):
        """Helper method to load a sound file with error handling"""
        try:
            if not os.path.exists(path):
                print(f"Warning: Sound file not found: {path}")
                return None
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Warning: Could not load sound file {path}: {e}")
            return None

    def play_sound(self, sound):
        """Play a sound effect if sound system is enabled and sound exists"""
        if self.sound_enabled and sound:
            try:
                self.effect_channel.play(sound)
            except Exception as e:
                print(f"Warning: Could not play sound: {e}")

    def start_music(self):
        """Start playing background music in a loop"""
        if self.sound_enabled and os.path.exists(self.soundtrack_path):
            try:
                pygame.mixer.music.load(self.soundtrack_path)
                pygame.mixer.music.set_volume(0.2)  # Set music volume
                pygame.mixer.music.play(-1, fade_ms=1000)  # -1 means loop indefinitely
            except Exception as e:
                print(f"Warning: Could not start music: {e}")

    def stop_music(self):
        """Stop background music"""
        if self.sound_enabled:
            try:
                pygame.mixer.music.fadeout(1000)
            except Exception as e:
                print(f"Warning: Could not stop music: {e}")

    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        if self.sound_enabled:
            try:
                pygame.mixer.music.set_volume(volume)
            except Exception as e:
                print(f"Warning: Could not set music volume: {e}")

    def play_card_flip(self):
        self.play_sound(self.card_flip)

    def play_card_place(self):
        self.play_sound(self.card_place)

    def play_foundation_complete(self):
        self.play_sound(self.foundation_complete)

    def play_game_win(self):
        self.play_sound(self.game_win)

    def play_game_over(self):
        self.play_sound(self.game_over)

    def play_error(self):
        self.play_sound(self.error)

    def __del__(self):
        """Cleanup when the object is destroyed"""
        try:
            pygame.mixer.quit()
            pygame.quit()
        except:
            pass


class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'

    @property
    def color(self):
        return 'red' if self in (Suit.HEARTS, Suit.DIAMONDS) else 'black'

    @property
    def symbol(self):
        return self.value


class Rank(Enum):
    ACE = (1, 'A')
    TWO = (2, '2')
    THREE = (3, '3')
    FOUR = (4, '4')
    FIVE = (5, '5')
    SIX = (6, '6')
    SEVEN = (7, '7')
    EIGHT = (8, '8')
    NINE = (9, '9')
    TEN = (10, '10')
    JACK = (11, 'J')
    QUEEN = (12, 'Q')
    KING = (13, 'K')

    @property
    def number(self):
        return self.value[0]

    @property
    def symbol(self):
        return self.value[1]


@dataclass
class Card:
    suit: Suit
    rank: Rank
    face_up: bool = False

    def __str__(self) -> str:
        if not self.face_up:
            return '[--]'
        return f'[{self.rank.symbol}{self.suit.symbol}]'

    def __repr__(self) -> str:
        return str(self)


class SolutionMove:
    def __init__(self, card: Card, source_type: str, source_idx: int,
                 dest_type: str, dest_idx: int):
        self.card = card
        self.source_type = source_type
        self.source_idx = source_idx
        self.dest_type = dest_type
        self.dest_idx = dest_idx


class GameGenerator:
    def __init__(self):
        self.solution_path = []

    def generate_solvable_game(self) -> Tuple[List[List[Card]], List[List[Card]],
    List[Card], List[SolutionMove]]:
        # Create a solved game state first
        all_cards = self._create_sorted_deck()

        # Create foundation piles (empty initially)
        foundation = [[] for _ in range(4)]

        # Create tableau with proper distribution
        tableau = [[] for _ in range(7)]
        stock = []

        # First, set aside cards for the tableau
        tableau_cards = []
        for i in range(7):
            for j in range(i + 1):
                card = all_cards.pop()
                tableau_cards.append(card)

        # Sort tableau cards to ensure solvability
        tableau_cards.sort(key=lambda c: (c.rank.number, hash(c.suit.value)))

        # Distribute cards to tableau
        card_index = 0
        for i in range(7):
            for j in range(i + 1):
                card = tableau_cards[card_index]
                card.face_up = (j == i)  # Only last card is face up
                tableau[i].append(card)
                card_index += 1

        # Remaining cards go to stock, arranged for solvability
        remaining_cards = all_cards
        remaining_cards.sort(key=lambda c: (c.rank.number, hash(c.suit.value)))
        stock = remaining_cards

        return tableau, foundation, stock, self.solution_path

    def _create_sorted_deck(self) -> List[Card]:
        """Create a full deck of cards"""
        cards = []
        for suit in Suit:
            for rank in Rank:
                cards.append(Card(suit, rank))

        # Shuffle but maintain some structure for solvability
        random.shuffle(cards)
        return cards

    def _ensure_solvability(self, tableau: List[List[Card]],
                            stock: List[Card]) -> None:
        """Adjust card positions to ensure the game is solvable"""
        # This would contain logic to verify and adjust card positions
        # to guarantee solvability
        pass


class VegasSolitaire:
    def __init__(self, screen):
        self.screen = screen
        self.generator = GameGenerator()

        # Game state
        self.bank = 0
        self.foundation = []
        self.stock = []
        self.waste = []
        self.solution_path = []
        self.debug_mode = False
        self.debug_info = []

        # UI state
        self.cursor = {'x': 0, 'y': 0}
        self.selected = None
        self.message = ""

        self._setup_colors()
        self.sounds = SoundEffects()


    """-----SETUP-----"""

    def _setup_colors(self):
        curses.start_color()
        if not curses.has_colors() or not curses.can_change_color():
            sys.exit("Your terminal does not support colors")

        # Reset any existing color pairs
        for i in range(1, curses.COLOR_PAIRS):
            try:
                curses.init_pair(i, 0, 0)
            except:
                break

        # Initialize our color pairs
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def new_game(self):
        self._setup_colors()
        self.bank -= 52
        self.tableau, self.foundation, self.stock, self.solution_path = \
            self.generator.generate_solvable_game()
        self.waste = []
        self.selected = None
        self.sounds.start_music()  # Start background music
        return True

    def _center_text(self, text, width, pad_char=" "):
        """Center text within given width with padding"""
        spaces = width - len(text)
        left_pad = spaces // 2
        right_pad = spaces - left_pad
        return f"{pad_char * left_pad}{text}{pad_char * right_pad}"

    def _show_main_menu(self):
        """Display main menu and get player choice"""
        BOX_WIDTH = 50  # Box width for the menu portion
        while True:
            self.screen.clear()
            max_y, max_x = self.screen.getmaxyx()

            # Create figlet text
            figlet = pyfiglet.Figlet(font=f"{MAIN_FIGLET_FONT}")
            title_text = figlet.renderText("Simit's")
            title_text += figlet.renderText("Solitaire")
            title_lines = title_text.rstrip().split('\n')

            # Calculate start positions
            title_y = max(0, (max_y - (len(title_lines) + 15)) // 2)  # +15 for menu items

            # Draw title
            for i, line in enumerate(title_lines):
                if title_y + i < max_y:
                    # Center each line of the figlet text
                    start_x = max(0, (max_x - len(line)) // 2)
                    self.screen.addstr(title_y + i, start_x, line, curses.color_pair(3))

            # Draw the menu box below the title
            menu_start_y = title_y + len(title_lines) + 2  # +2 for spacing
            menu_start_x = max(0, (max_x - BOX_WIDTH) // 2)

            # Draw menu items with box
            menu_items = [
                "┌" + "─" * (BOX_WIDTH - 2) + "┐",
                "│" + self._center_text("♠ ♥ ♣ ♦", BOX_WIDTH - 2) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│" + self._center_text("[N] NEW GAME", BOX_WIDTH - 2) + "│",
                "│" + self._center_text("[Q] QUIT", BOX_WIDTH - 2) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│" + self._center_text("RULES", BOX_WIDTH - 2) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│ • Entry Fee: $52" + " " * (BOX_WIDTH - 19) + "│",
                "│ • $5 per Foundation Card" + " " * (BOX_WIDTH - 27) + "│",
                "│ • Win Bonus: $100" + " " * (BOX_WIDTH - 20) + "│",
                "│ • Hint Cost: $5" + " " * (BOX_WIDTH - 18) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│" + self._center_text("© VXCO GAMES", BOX_WIDTH - 2) + "│",
                "└" + "─" * (BOX_WIDTH - 2) + "┘"
            ]

            # Draw menu box and items
            for i, item in enumerate(menu_items):
                if menu_start_y + i < max_y:
                    if "NEW GAME" in item:
                        self.screen.addstr(menu_start_y + i, menu_start_x, item, curses.color_pair(2))
                    elif "QUIT" in item:
                        self.screen.addstr(menu_start_y + i, menu_start_x, item, curses.color_pair(1))
                    else:
                        self.screen.addstr(menu_start_y + i, menu_start_x, item, curses.color_pair(3))

            self.screen.refresh()

            # Handle input
            key = self.screen.getch()
            if key in (ord('n'), ord('N')):
                return True
            elif key in (ord('q'), ord('Q')):
                return False

    def _show_game_over_screen(self, won=False):
        self.sounds.stop_music()
        """Display game over screen with final score"""
        BOX_WIDTH = 50
        while True:
            self.screen.clear()
            max_y, max_x = self.screen.getmaxyx()

            # Create figlet text
            figlet = pyfiglet.Figlet(font=f'{PYFIGLET_FONT}')
            result_text = "Victory!" if won else "Game Over"
            figlet_text = figlet.renderText(result_text)
            text_lines = figlet_text.rstrip().split('\n')

            # Calculate start positions
            title_y = max(0, (max_y - (len(text_lines) + 8)) // 2)

            # Draw figlet text
            for i, line in enumerate(text_lines):
                if title_y + i < max_y:
                    start_x = max(0, (max_x - len(line)) // 2)
                    color = curses.color_pair(2) if won else curses.color_pair(1)
                    self.screen.addstr(title_y + i, start_x, line, color)

            # Draw result box below figlet text
            box_y = title_y + len(text_lines) + 2
            box_start_x = max(0, (max_x - BOX_WIDTH) // 2)

            result_box = [
                "┌" + "─" * (BOX_WIDTH - 2) + "┐",
                "│" + self._center_text(f"FINAL BANK: ${self.bank}", BOX_WIDTH - 2) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│" + self._center_text("[N] NEW GAME    [Q] QUIT", BOX_WIDTH - 2) + "│",
                "└" + "─" * (BOX_WIDTH - 2) + "┘"
            ]

            # Draw result box
            color = curses.color_pair(2) if won else curses.color_pair(1)
            for i, line in enumerate(result_box):
                if box_y + i < max_y:
                    self.screen.addstr(box_y + i, box_start_x, line, color)

            self.screen.refresh()

            # Handle input
            key = self.screen.getch()
            if key in (ord('n'), ord('N')):
                return True
            elif key in (ord('q'), ord('Q')):
                return False

    def run(self):
        # Show main menu first
        if not self._show_main_menu():
            return

        self.sounds.start_music()  # Start music when game starts

        while True:
            if not self.new_game():
                self.sounds.stop_music()  # Stop music if quitting
                return

            game_running = True
            while game_running:
                self._draw_screen()
                if not self._handle_input():
                    return

                if self._check_win():
                    self.message = f"You won! Bank: ${self.bank}"
                    self._draw_screen()
                    self.screen.getch()
                    game_running = False
                    if not self._show_game_over_screen(won=True):
                        return

                if self._check_game_over():
                    self._draw_screen()
                    self.screen.getch()
                    game_running = False
                    if not self._show_game_over_screen(won=False):
                        return

    """-----CLI ACTIONS-----"""

    def _debug_print(self, message):
        """Add message to debug info"""
        self.debug_info.append(f"DEBUG: {message}")
        if len(self.debug_info) > 10:  # Keep last 10 messages
            self.debug_info.pop(0)

    def _draw_screen(self):
        try:
            self.screen.clear()
            max_y, max_x = self.screen.getmaxyx()

            # Fixed card dimensions and spacing
            CARD_WIDTH = 6  # [A♠]
            MIN_SPACING = 2  # Minimum space between cards
            MAX_SPACING = 3  # Maximum space between cards
            TOTAL_COLUMNS = 7

            # Calculate maximum tableau height (for vertical centering)
            max_tableau_height = max(len(pile) for pile in self.tableau)
            total_height = max_tableau_height + 7  # 5 for top area, 2 for padding

            # Calculate vertical centering
            top_margin = max(0, (max_y - total_height) // 2)

            # Calculate the ideal game width
            ideal_game_width = (CARD_WIDTH * TOTAL_COLUMNS) + (MIN_SPACING * (TOTAL_COLUMNS - 1))
            max_game_width = (CARD_WIDTH * TOTAL_COLUMNS) + (MAX_SPACING * (TOTAL_COLUMNS - 1))

            # Calculate horizontal centering
            left_margin = max(2, (max_x - max_game_width) // 2)

            # Calculate column positions with controlled spacing
            column_x = []
            spacing = min(MAX_SPACING, max(MIN_SPACING,
                                           (max_x - (2 * left_margin) - (TOTAL_COLUMNS * CARD_WIDTH)) // (
                                                   TOTAL_COLUMNS - 1)))

            current_x = left_margin
            for i in range(TOTAL_COLUMNS):
                column_x.append(current_x)
                current_x += CARD_WIDTH + spacing

            # Draw header
            header_y = top_margin
            header = f"Bank: ${self.bank}   [Q:Quit, N:New Game, H:Hint(-5$)]"
            self.screen.addstr(header_y, left_margin, header[:max_x - left_margin], curses.color_pair(2))

            if self.message:
                self.screen.addstr(header_y + 1, left_margin, self.message[:max_x - left_margin], curses.color_pair(3))

            # Draw stock and waste piles
            stock_y = header_y + 3
            if stock_y < max_y:
                # Stock
                stock_str = "[##]" if self.stock else "[  ]"
                if self.cursor['y'] == 0 and self.cursor['x'] == 0:
                    self.screen.addstr(stock_y, column_x[0], stock_str, curses.A_REVERSE)
                else:
                    self.screen.addstr(stock_y, column_x[0], stock_str)

                # Draw waste
                waste_x = column_x[0] + CARD_WIDTH + 2
                if self.waste and waste_x + (3 * CARD_WIDTH) < max_x:
                    visible_waste = self.waste[-3:] if len(self.waste) >= 3 else self.waste
                    for idx, card in enumerate(visible_waste):
                        waste_str = str(card)
                        display_x = waste_x + (idx * 3)  # Overlapped waste cards

                        if display_x + len(waste_str) < max_x:
                            is_selected = (self.cursor['y'] == 0 and
                                           self.cursor['x'] == 1 and
                                           idx == len(visible_waste) - 1)

                            if is_selected:
                                self.screen.addstr(stock_y, display_x, waste_str, curses.A_REVERSE)
                            else:
                                if card.suit.color == 'red':
                                    self.screen.addstr(stock_y, display_x, waste_str, curses.color_pair(1))
                                else:
                                    self.screen.addstr(stock_y, display_x, waste_str)
                elif waste_x < max_x:
                    self.screen.addstr(stock_y, waste_x, "[  ]")

                # Draw foundations - centered in remaining space
                foundation_start = column_x[3]  # Start from middle column
                foundation_spacing = min(MAX_SPACING, CARD_WIDTH)
                for i in range(4):
                    x = foundation_start + (i * (CARD_WIDTH + foundation_spacing))
                    if x + CARD_WIDTH < max_x:
                        if i < len(self.foundation):
                            if self.foundation[i]:
                                card_str = str(self.foundation[i][-1])
                                if self.cursor['y'] == 0 and self.cursor['x'] == i + 2:
                                    self.screen.addstr(stock_y, x, card_str, curses.A_REVERSE)
                                else:
                                    if self.foundation[i][-1].suit.color == 'red':
                                        self.screen.addstr(stock_y, x, card_str, curses.color_pair(1))
                                    else:
                                        self.screen.addstr(stock_y, x, card_str)
                            else:
                                empty_str = "[  ]"
                                if self.cursor['y'] == 0 and self.cursor['x'] == i + 2:
                                    self.screen.addstr(stock_y, x, empty_str, curses.A_REVERSE)
                                else:
                                    self.screen.addstr(stock_y, x, empty_str)

            # Draw tableau
            tableau_y = stock_y + 2
            for i in range(TOTAL_COLUMNS):
                x = column_x[i]
                if x + CARD_WIDTH >= max_x:
                    break

                if tableau_y < max_y:
                    if not self.tableau[i]:
                        empty_slot = "[   ]"
                        if self.cursor['y'] == 1 and self.cursor['x'] == i:
                            self.screen.addstr(tableau_y, x, empty_slot, curses.A_REVERSE)
                        else:
                            self.screen.addstr(tableau_y, x, empty_slot, curses.color_pair(2))

                    for j, card in enumerate(self.tableau[i]):
                        y = tableau_y + j
                        if y >= max_y:
                            break

                        card_str = str(card)
                        attrs = curses.A_NORMAL
                        if self.cursor['y'] == j + 1 and self.cursor['x'] == i:
                            attrs = curses.A_REVERSE
                        elif self.selected and self.selected[0] == 'tableau' and \
                                self.selected[1] == i and self.selected[2] <= j:
                            attrs = curses.A_REVERSE

                        if card.face_up and card.suit.color == 'red':
                            self.screen.addstr(y, x, card_str, curses.color_pair(1) | attrs)
                        else:
                            self.screen.addstr(y, x, card_str, attrs)

            # Debug info with adjusted position
            if self.debug_mode:
                debug_start_y = max_y - 12
                if debug_start_y > tableau_y + max_tableau_height + 2:
                    self.screen.addstr(debug_start_y, left_margin, "=== DEBUG INFO ===", curses.color_pair(3))
                    self.screen.addstr(debug_start_y + 1, left_margin, f"Cursor: {self.cursor}")
                    self.screen.addstr(debug_start_y + 2, left_margin, f"Selected: {self.selected}")
                    self.screen.addstr(debug_start_y + 3, left_margin, f"Screen: {max_y}x{max_x}")

                    moves = self._get_possible_moves()
                    if moves:
                        self.screen.addstr(debug_start_y + 4, left_margin, "Possible moves:")
                        for i, move in enumerate(moves):
                            if debug_start_y + 5 + i < max_y:
                                self.screen.addstr(debug_start_y + 5 + i, left_margin + 2,
                                                   move[:max_x - left_margin - 3])

            self.screen.refresh()
        except Exception as e:
            self._debug_print(f"Draw error: {str(e)}")

    def _find_next_valid_position(self, current_x, current_y, direction):
        """Find next valid cursor position, returns (x, y)"""
        if current_y == 0:  # Top row
            # Define valid positions in top row: stock, waste, foundations
            valid_x = [0]  # Stock always valid
            if self.waste:  # Waste if not empty
                valid_x.append(1)
            # Add foundation positions
            valid_x.extend([i + 2 for i in range(4)])

            # Find next valid x
            if direction > 0:  # Moving right
                next_positions = [x for x in valid_x if x > current_x]
                return min(next_positions) if next_positions else current_x, current_y
            else:  # Moving left
                next_positions = [x for x in valid_x if x < current_x]
                return max(next_positions) if next_positions else current_x, current_y

        else:  # Tableau rows
            if current_y == 1:  # First tableau row
                # Only consider columns that have cards or are empty (valid for placement)
                valid_x = [i for i in range(7) if self.tableau[i] or
                           (self.selected and self._can_move_to_tableau(self._get_selected_cards()[0], i))]
            else:
                # Only consider columns that have cards at this row
                valid_x = [i for i in range(7) if len(self.tableau[i]) >= current_y]

            if not valid_x:  # No valid positions found
                return current_x, current_y

            if direction > 0:  # Moving right
                next_positions = [x for x in valid_x if x > current_x]
                return min(next_positions) if next_positions else current_x, current_y
            else:  # Moving left
                next_positions = [x for x in valid_x if x < current_x]
                return max(next_positions) if next_positions else current_x, current_y

    def _handle_input(self):
        try:
            key = self.screen.getch()

            if key == ord('q'):
                return False
            elif key == ord('n'):
                return self.new_game()
            elif key == ord('d'):
                self.debug_mode = not self.debug_mode
                self._debug_print("Debug mode toggled")
                return True
            elif key == ord('h'):
                self._show_hint()
                return True

            # Store previous position for invalid move handling
            prev_x, prev_y = self.cursor['x'], self.cursor['y']

            # Handle movement with bounds checking
            if key == curses.KEY_UP and self.cursor['y'] > 0:
                if self.cursor['y'] == 1:  # Moving from tableau to top row
                    # Map tableau columns to top row elements
                    if self.cursor['x'] <= 1:  # First two columns go to stock/waste
                        self.cursor['x'] = min(self.cursor['x'], 1)
                    else:  # Other columns map to foundations
                        self.cursor['x'] = min(self.cursor['x'] - 1, 5)
                self.cursor['y'] -= 1
            elif key == curses.KEY_DOWN:
                max_y = max(len(pile) for pile in self.tableau)
                if self.cursor['y'] == 0:  # Moving from top row
                    # Map top row elements to tableau columns
                    if self.cursor['x'] <= 1:  # Stock/waste go to first two columns
                        self.cursor['x'] = min(self.cursor['x'], 1)
                    else:  # Foundations map to tableau columns
                        self.cursor['x'] = min(self.cursor['x'] + 1, 6)
                    if self._is_valid_position(self.cursor['x'], 1):
                        self.cursor['y'] = 1
                else:
                    new_y = min(self.cursor['y'] + 1, max_y + 1)
                    if self._is_valid_position(self.cursor['x'], new_y):
                        self.cursor['y'] = new_y
            elif key == curses.KEY_LEFT:
                new_x, new_y = self._find_next_valid_position(self.cursor['x'], self.cursor['y'], -1)
                self.cursor['x'], self.cursor['y'] = new_x, new_y
            elif key == curses.KEY_RIGHT:
                new_x, new_y = self._find_next_valid_position(self.cursor['x'], self.cursor['y'], 1)
                self.cursor['x'], self.cursor['y'] = new_x, new_y
            elif key == ord(' '):
                try:
                    if not self._handle_selection():
                        # If selection was invalid, keep the cursor where it was
                        self.cursor['x'], self.cursor['y'] = prev_x, prev_y
                        self.selected = None  # Reset selection on invalid move
                except Exception as e:
                    self._debug_print(f"Selection error: {str(e)}")

            return True
        except Exception as e:
            self._debug_print(f"Input error: {str(e)}")
            return True

    def _is_valid_position(self, x, y) -> bool:
        """Check if the position has a card or is a valid empty spot"""
        if y == 0:  # Top row (stock, waste, foundations)
            return x <= 5  # Allow movement across all top row positions

        # Tableau positions
        if x >= len(self.tableau):
            return False

        # Allow movement to empty tableau slots when y is 1 (first row of tableau)
        if y == 1:
            if not self.tableau[x]:
                return True
            return True

        # For other rows, check if there's a card at this position
        if y - 1 < len(self.tableau[x]):
            return True

        # When moving selected cards, only allow movement to valid destinations
        if self.selected:
            dest_pile = self.tableau[x]
            return y - 1 == len(dest_pile) and self._can_move_to_tableau(self._get_selected_cards()[0], x)

        return False

    """-----GAME LOGIC-----"""

    def _get_possible_moves(self) -> List[str]:
        """Get list of all possible moves in current state"""
        moves = []

        # Check waste to foundation/tableau
        if self.waste:
            card = self.waste[-1]
            self._debug_print(f"Checking waste card: {card}")

            # Check foundations
            for i in range(4):
                if self._can_move_to_foundation(card, i):
                    moves.append(f"Waste {card} → Foundation {i + 1}")

            # Check tableau
            for i in range(7):
                if self._can_move_to_tableau(card, i):
                    moves.append(f"Waste {card} → Tableau {i + 1}")

        # Check tableau to foundation/tableau
        for i in range(7):
            if not self.tableau[i]:
                continue

            for j in range(len(self.tableau[i])):
                if not self.tableau[i][j].face_up:
                    continue

                card = self.tableau[i][j]
                cards = self.tableau[i][j:]
                self._debug_print(f"Checking tableau {i + 1} card: {card}")

                # Check foundations
                for k in range(4):
                    if self._can_move_to_foundation(card, k):
                        moves.append(f"Tableau {i + 1} {card} → Foundation {k + 1}")

                # Check tableau
                for k in range(7):
                    if k != i and self._can_move_to_tableau(card, k):
                        moves.append(f"Tableau {i + 1} {','.join(map(str, cards))} → Tableau {k + 1}")

        return moves

    def _handle_selection(self) -> bool:
        """Handle card selection and movement. Returns True if valid move was made."""
        # Handle stock pile
        if self.cursor['y'] == 0 and self.cursor['x'] == 0:
            if self.stock:
                card = self.stock.pop()
                card.face_up = True
                self.waste.append(card)
                self.sounds.play_card_flip()
                return True
            self.sounds.play_error()
            return False

        # Handle waste pile
        if self.cursor['y'] == 0 and self.cursor['x'] == 1:
            if not self.waste:
                return False

            if self.selected:
                self.selected = None
            else:
                self.selected = ('waste', 0, len(self.waste) - 1)
            return True

        # Handle foundation
        if self.cursor['y'] == 0 and self.cursor['x'] >= 2:
            foundation_idx = self.cursor['x'] - 2
            if self.selected:
                return self._try_move_to_foundation(foundation_idx)
            return False

        # Handle tableau
        tableau_idx = self.cursor['x']
        card_idx = self.cursor['y'] - 1

        # Handle empty tableau slot
        if not self.tableau[tableau_idx] or card_idx >= len(self.tableau[tableau_idx]):
            if self.selected:
                return self._try_move_to_tableau(tableau_idx)
            return False

        if self.selected:
            success = self._try_move_to_tableau(tableau_idx)
            if not success:
                self.selected = None
            return success
        else:
            if self.tableau[tableau_idx][card_idx].face_up:
                self.selected = ('tableau', tableau_idx, card_idx)
                return True
        return False

    def _get_selected_cards(self):
        """Helper to get currently selected card(s)"""
        if not self.selected:
            return []

        source_type, source_idx, card_idx = self.selected

        if source_type == 'waste':
            return [self.waste[-1]]
        else:  # tableau
            return self.tableau[source_idx][card_idx:]

    def _try_move_to_foundation(self, foundation_idx) -> bool:
        """Try to move a card to foundation. Returns True if successful."""
        if not self.selected:
            self.sounds.play_error()
            return False

        source_type, source_idx, card_idx = self.selected

        if source_type == 'waste':
            card = self.waste[-1]
        else:  # tableau
            card = self.tableau[source_idx][card_idx]

        if self._can_move_to_foundation(card, foundation_idx):
            if source_type == 'waste':
                self.waste.pop()
            else:
                self.tableau[source_idx] = self.tableau[source_idx][:card_idx]
                if self.tableau[source_idx] and not self.tableau[source_idx][-1].face_up:
                    self.tableau[source_idx][-1].face_up = True

            self.foundation[foundation_idx].append(card)
            self.bank += 5
            self.selected = None

            if len(self.foundation[foundation_idx]) == 13:
                self.sounds.play_foundation_complete()
            else:
                self.sounds.play_card_place()

            return True

        self.sounds.play_error()
        return False

    def _try_move_to_tableau(self, tableau_idx) -> bool:
        """Try to move card(s) to tableau. Returns True if successful."""
        if not self.selected:
            self.sounds.play_error()
            return False

        source_type, source_idx, card_idx = self.selected

        if source_type == 'waste':
            card = self.waste[-1]
            cards = [card]
        else:  # tableau
            cards = self.tableau[source_idx][card_idx:]

        if self._can_move_to_tableau(cards[0], tableau_idx):
            if source_type == 'waste':
                self.waste.pop()
            else:
                self.tableau[source_idx] = self.tableau[source_idx][:card_idx]
                if self.tableau[source_idx] and not self.tableau[source_idx][-1].face_up:
                    self.tableau[source_idx][-1].face_up = True

            self.tableau[tableau_idx].extend(cards)
            self.selected = None
            self.sounds.play_card_place()
            return True

        self.sounds.play_error()
        return False

    def _can_move_to_foundation(self, card, foundation_idx):
        if not card.face_up:
            self._debug_print(f"Card {card} is not face up")
            return False

        # Check if card has cards on top of it in tableau
        for pile in self.tableau:
            if card in pile:
                card_index = pile.index(card)
                if card_index < len(pile) - 1:
                    self._debug_print(f"Card {card} has cards on top of it")
                    return False

        foundation = self.foundation[foundation_idx]

        if not foundation:
            result = card.rank == Rank.ACE
            self._debug_print(f"Empty foundation: requires Ace, got {card.rank.symbol}")
            return result

        top_card = foundation[-1]
        result = (card.suit == top_card.suit and
                  card.rank.number == top_card.rank.number + 1)
        self._debug_print(f"Foundation move {card} on {top_card}: {result}")
        return result

    def _can_move_to_tableau(self, card, tableau_idx):
        """Check if card can be moved to tableau pile"""
        if not card.face_up:
            self._debug_print(f"Card {card} is not face up")
            return False

        tableau = self.tableau[tableau_idx]

        if not tableau:
            result = card.rank == Rank.KING
            self._debug_print(f"Empty tableau: requires King, got {card.rank.symbol}")
            return result

        top_card = tableau[-1]
        result = (top_card.face_up and
                  card.suit.color != top_card.suit.color and
                  card.rank.number == top_card.rank.number - 1)
        self._debug_print(f"Tableau move {card} on {top_card}: {result}")
        return result

    def _check_win(self):
        if all(len(pile) == 13 for pile in self.foundation):
            bonus = 100
            self.bank += bonus
            self.message = f"You won! Bank: ${self.bank} (Bonus: +${bonus})"
            self.sounds.play_game_win()
            return True
        return False

    def _check_game_over(self):
        is_game_over = not self.stock
        if is_game_over:
            self.sounds.play_game_over()
        return is_game_over

    def _has_valid_moves(self):
        # Check waste to foundation/tableau
        if self.waste:
            card = self.waste[-1]
            # Check foundations
            for i in range(4):
                if self._can_move_to_foundation(card, i):
                    return True
            # Check tableau
            for i in range(7):
                if self._can_move_to_tableau(card, i):
                    return True

        # Check tableau to foundation/tableau
        for i in range(7):
            for j in range(len(self.tableau[i])):
                if not self.tableau[i][j].face_up:
                    continue

                card = self.tableau[i][j]
                # Check foundations
                for k in range(4):
                    if self._can_move_to_foundation(card, k):
                        return True
                # Check tableau
                for k in range(7):
                    if k != i and self._can_move_to_tableau(card, k):
                        return True

        return False

    def _show_hint(self):
        self.bank -= 5
        moves = self._get_possible_moves()
        if moves:
            # Sort moves by priority
            prioritized_moves = self._prioritize_moves(moves)
            self.message = f"Hint (-$5): {prioritized_moves[0]}"
        else:
            self.message = "Hint (-$5): Deal a card from the stock"

    def _prioritize_moves(self, moves):
        # Hint Prioritization:
        # 1. Foundation
        # 2. Revealing face-down
        # 3. Moving kings to empty
        # 4. Other tableau moves
        foundation_moves = [m for m in moves if "→ Foundation" in m]
        reveal_moves = [m for m in moves if "reveal" in m.lower()]
        king_moves = [m for m in moves if "King" in m and "empty" in m.lower()]
        other_moves = [m for m in moves if m not in foundation_moves + reveal_moves + king_moves]

        return foundation_moves + reveal_moves + king_moves + other_moves


def main(stdscr):
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(1)  # Enable keypad

    game = VegasSolitaire(stdscr)
    game.run()


if __name__ == '__main__':
    # Quick sound test before starting the game
    sounds = SoundEffects()
    if sounds.sound_enabled:
        print("Sound system initialized successfully")
        sounds.play_card_flip()
        pygame.time.wait(1000)  # Wait 1 second to hear the sound
    else:
        print("Sound system failed to initialize")

    curses.wrapper(main)
