import curses
import os
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set, Dict
from enum import Enum
import sys
import pyfiglet
import pygame

import logging
from datetime import datetime
import traceback

import uuid
import platform


MAIN_FIGLET_FONT = 'graffiti'
PYFIGLET_FONT = 'slant'


class ArgosLogger:
    HEADER = '[ARGOS@SSOLIT]'

    # ANSI color codes - will only be used if terminal supports it
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]  # Create unique session ID
        self.logger = logging.getLogger(f'ArgosLogger-{self.session_id}')
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        self.log_dir = 'logs'
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Set up latest.log symlink/file path
        self.latest_log_path = os.path.join(self.log_dir, 'latest.log')

        # Generate filename with timestamp and session ID
        timestamp = datetime.now().strftime('%Y%m%d_%H-%M-%S')
        self.current_log_file = os.path.join(self.log_dir, f'ssolit_{timestamp}_{self.session_id}.log')

        # Set up handlers
        self._setup_handlers()

        # Log initial session info
        self.info(f"Session started - ID: {self.session_id}")

        # Update latest.log link/file
        self._update_latest_log()

    def _setup_handlers(self):
        # File handler for current log file
        file_handler = logging.FileHandler(self.current_log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s %(name)s -> %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console formatter - checks if terminal supports colors
        if self._supports_color():
            console_formatter = logging.Formatter('%(message)s')
        else:
            # Strip ANSI codes if terminal doesn't support colors
            console_formatter = logging.Formatter(
                '[ARGOS@SSOLIT] %(asctime)s -> %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        # Remove any existing handlers
        self.logger.handlers = []

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _update_latest_log(self):
        """Update the latest.log to point to the current log file"""
        try:
            # Remove existing latest.log if it exists
            if os.path.exists(self.latest_log_path):
                os.remove(self.latest_log_path)

            # On Windows, we can't create symlinks easily, so copy the file instead
            if platform.system() == 'Windows':
                with open(self.current_log_file, 'r') as source:
                    with open(self.latest_log_path, 'w') as target:
                        target.write(source.read())
            else:
                # Create symbolic link on Unix-like systems
                os.symlink(self.current_log_file, self.latest_log_path)
        except Exception as e:
            print(f"Warning: Could not update latest.log: {e}")

    def _supports_color(self):
        """Check if the terminal supports color output"""
        plat = platform.system()
        supported_platform = plat != 'Windows' or 'ANSICON' in os.environ
        is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        return supported_platform and is_a_tty

    def _format_message(self, level, message):
        """Format message with colors if supported"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self._supports_color():
            color = self.COLORS.get(level, '')
            reset = self.COLORS['RESET']
            return f"{color}{self.HEADER} {timestamp} -> {level} | {message}{reset}"
        else:
            return f"{self.HEADER} {timestamp} -> {level} | {message}"

    def debug(self, message):
        formatted = self._format_message('DEBUG', message)
        self.logger.debug(formatted)
        self._update_latest_log()

    def info(self, message):
        formatted = self._format_message('INFO', message)
        self.logger.info(formatted)
        self._update_latest_log()

    def warning(self, message):
        formatted = self._format_message('WARNING', message)
        self.logger.warning(formatted)
        self._update_latest_log()

    def error(self, message, exc_info=None):
        if exc_info:
            tb = ''.join(traceback.format_exception(*exc_info))
            message = f"{message}\n{tb}"
        formatted = self._format_message('ERROR', message)
        self.logger.error(formatted)
        self._update_latest_log()

    def critical(self, message, exc_info=None):
        if exc_info:
            tb = ''.join(traceback.format_exception(*exc_info))
            message = f"{message}\n{tb}"
        formatted = self._format_message('CRITICAL', message)
        self.logger.critical(formatted)
        self._update_latest_log()

    def exception(self, message):
        """Automatically logs the current exception information"""
        formatted = self._format_message('ERROR', message)
        self.logger.exception(formatted)
        self._update_latest_log()

    def get_latest_log_path(self):
        """Return the path to the latest log file"""
        return self.latest_log_path

    def get_session_id(self):
        """Return the current session ID"""
        return self.session_id


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


class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


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

    def __hash__(self):
        # Hash based on suit and rank (face_up status doesn't matter for identity)
        return hash((self.suit, self.rank))

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank



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

    def generate_solvable_game(self, difficulty: Difficulty) -> Tuple[
        List[List[Card]], List[List[Card]], List[Card], List[SolutionMove]]:
        # Build game from foundation-up to ensure solvability
        tableau, stock = self._build_solvable_layout(difficulty)
        foundation = [[] for _ in range(4)]
        return tableau, foundation, stock, self.solution_path

    def _build_solvable_layout(self, difficulty: Difficulty) -> Tuple[List[List[Card]], List[Card]]:
        deck = self._create_deck()
        tableau = [[] for _ in range(7)]

        # Organize cards by suit and rank for controlled distribution
        organized = self._organize_cards(deck, difficulty)

        # Build tableau ensuring valid move sequences exist
        remaining = self._build_tableau(tableau, organized, difficulty)

        # Arrange stock for desired difficulty
        stock = self._arrange_stock(remaining, difficulty)

        return tableau, stock

    def _organize_cards(self, deck: List[Card], difficulty: Difficulty) -> Dict[Suit, List[Card]]:
        organized = {suit: [] for suit in Suit}
        for card in deck:
            organized[card.suit].append(card)

        # Sort each suit's cards
        for suit in organized:
            organized[suit].sort(key=lambda c: c.rank.number)

        if difficulty == Difficulty.HARD:
            # Maximize interference between suits
            for suit in organized:
                random.shuffle(organized[suit])

        return organized

    def _build_tableau(self, tableau: List[List[Card]], organized: Dict[Suit, List[Card]], difficulty: Difficulty) -> \
    List[Card]:
        remaining_cards = []
        foundation_bases = []

        # Reserve some aces and twos for stock based on difficulty
        if difficulty == Difficulty.EASY:
            reserve_count = 2
        elif difficulty == Difficulty.MEDIUM:
            reserve_count = 3
        else:
            reserve_count = 4

        # Extract cards for foundation bases
        for suit in organized:
            foundation_bases.extend(organized[suit][:reserve_count])
            organized[suit] = organized[suit][reserve_count:]

        # Build tableau ensuring valid sequences
        for i in range(7):
            cards_needed = i + 1
            tableau_cards = []

            # Build valid sequence for face-up card
            last_card = self._select_tableau_card(organized, difficulty)
            tableau_cards.append(last_card)

            # Fill face-down cards ensuring future moves possible
            while len(tableau_cards) < cards_needed:
                card = self._select_compatible_card(organized, last_card, difficulty)
                tableau_cards.append(card)

            # Place cards in tableau
            for j, card in enumerate(tableau_cards):
                card.face_up = (j == len(tableau_cards) - 1)  # faceupp
                tableau[i].append(card)

        # Collect remaining cards
        for suit in organized:
            remaining_cards.extend(organized[suit])
        remaining_cards.extend(foundation_bases)

        return remaining_cards

    def _select_tableau_card(self, organized: Dict[Suit, List[Card]], difficulty: Difficulty) -> Card:
        suits = list(organized.keys())
        if difficulty == Difficulty.EASY:
            # Prefer higher cards for easier building
            for suit in suits:
                if organized[suit] and organized[suit][-1].rank.number > 10:
                    return organized[suit].pop()

        # Select random card ensuring move possibilities
        suit = random.choice(suits)
        while not organized[suit]:
            suits.remove(suit)
            if not suits:
                return None
            suit = random.choice(suits)

        return organized[suit].pop()

    def _select_compatible_card(self, organized: Dict[Suit, List[Card]], target: Card, difficulty: Difficulty) -> Card:
        valid_suits = [suit for suit in organized if organized[suit]]
        if not valid_suits:
            return None

        if difficulty == Difficulty.EASY:
            # Select cards that enable easier sequences
            #compatible_suits = [s for s in valid_suits if s.color != target.suit.color]
            compatible_suits = valid_suits #I needed this...
        else:
            # More random selection for higher difficulties
            compatible_suits = valid_suits

        suit = random.choice(compatible_suits)
        return organized[suit].pop()

    def _arrange_stock(self, cards: List[Card], difficulty: Difficulty) -> List[Card]:
        if difficulty == Difficulty.EASY:
            # Put aces and important cards near top
            cards.sort(key=lambda c: (
                c.rank != Rank.ACE,
                c.rank != Rank.TWO,
                random.random()
            ))
        elif difficulty == Difficulty.MEDIUM:
            # Semi-random arrangement while maintaining some structure
            sorted_cards = sorted(cards, key=lambda c: (c.suit.value, c.rank.number))
            chunks = [sorted_cards[i:i + 4] for i in range(0, len(sorted_cards), 4)]
            random.shuffle(chunks)
            cards = [card for chunk in chunks for card in chunk]
        else:  # HARD
            # Group cards by suit
            suit_groups = {suit: [] for suit in Suit}
            for card in cards:
                suit_groups[card.suit].append(card)

            # For each suit, arrange cards in foundation-building dependencies
            arranged_cards = []

            def analyze_suit_dependencies(suit_cards):
                """Create groups of cards based on their dependencies for foundation building"""
                # Sort cards by rank for initial analysis
                suit_cards.sort(key=lambda c: c.rank.number)

                # Group cards into building phases
                phases = []
                current_phase = []
                sequence_start = None

                for card in suit_cards:
                    if not sequence_start:
                        sequence_start = card.rank.number
                        current_phase.append(card)
                    else:
                        # If there's a gap in the sequence, start a new phase
                        if card.rank.number != sequence_start + len(current_phase):
                            if current_phase:
                                phases.append(current_phase)
                            current_phase = []
                            sequence_start = card.rank.number
                        current_phase.append(card)

                if current_phase:
                    phases.append(current_phase)

                return phases

            # Process each suit's dependencies and interleave them
            all_phases = []
            for suit in Suit:
                if suit_groups[suit]:
                    phases = analyze_suit_dependencies(suit_groups[suit])
                    all_phases.extend(phases)

            # Shuffle phases to create interesting but solvable combinations
            random.shuffle(all_phases)

            # Interleave cards from different phases
            while all_phases:
                # Randomly select a phase that still has cards
                available_phases = [p for p in all_phases if p]
                if not available_phases:
                    break

                selected_phase = random.choice(available_phases)

                # Take a card from the selected phase
                card = selected_phase.pop(0)
                arranged_cards.append(card)

                # Remove empty phases
                all_phases = [p for p in all_phases if p]

                # Occasionally insert a card from a different suit to increase difficulty
                if random.random() < 0.3 and len(all_phases) > 1:
                    other_phases = [p for p in all_phases if p != selected_phase]
                    if other_phases:
                        other_phase = random.choice(other_phases)
                        if other_phase:
                            card = other_phase.pop(0)
                            arranged_cards.append(card)

            cards = arranged_cards

        # Set all stock cards face-down
        for card in cards:
            card.face_up = False

        return cards

    def _create_deck(self) -> List[Card]:
        return [Card(suit, rank) for suit in Suit for rank in Rank]


def suit_to_idx(suit: Suit) -> int:
    """Helper function to convert suit to foundation index"""
    return {'♥': 0, '♦': 1, '♣': 2, '♠': 3}[suit.symbol]


class VegasSolitaire:
    def __init__(self, screen):
        self.screen = screen
        self.generator = GameGenerator()

        self.logger = ArgosLogger()
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
        self.message_timer = 0

        self._setup_colors()
        self.sounds = SoundEffects()

        self.last_move_time = time.time()
        self.hint_highlighted = False
        self.stuck_timer_started = False

        self._solvability_cache = None
        self._last_state_hash = None
        self._calculation_stats = {
            'running': False,
            'states_checked': 0,
            'current_depth': 0,
            'deepest_depth': 0,
            'start_time': 0,
            'result': None
        }

        self.logger.info("Game initialized")

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

    def new_game(self, difficulty: Difficulty = Difficulty.EASY):
        try:
            self.logger.info(f"Starting new game with difficulty: {difficulty.name}")
            self._setup_colors()
            self.bank -= 52
            self.tableau, self.foundation, self.stock, self.solution_path = \
                self.generator.generate_solvable_game(difficulty)
            self.waste = []
            self.selected = None
            self.sounds.start_music()
            self.logger.info("New game started successfully")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to start new game: {str(e)}")
            return False

    def _center_text(self, text, width, pad_char=" "):
        """Center text within given width with padding"""
        spaces = width - len(text)
        left_pad = spaces // 2
        right_pad = spaces - left_pad
        return f"{pad_char * left_pad}{text}{pad_char * right_pad}"


    def _show_main_menu(self):
        """Display main menu and get player choice"""
        BOX_WIDTH = 50  # Box width for the menu portion
        current_difficulty = Difficulty.HARD
        while True:
            self.screen.clear()
            max_y, max_x = self.screen.getmaxyx()

            # Create figlet text
            figlet = pyfiglet.Figlet(font=f"{MAIN_FIGLET_FONT}")
            title_text = figlet.renderText("Simitaire")
            title_lines = title_text.rstrip().split('\n')

            # Calculate start positions
            title_y = max(0, (max_y - (len(title_lines) + 15)) // 2)  # +15 for menu items

            # Draw title
            for i, line in enumerate(title_lines):
                if title_y + i < max_y:
                    # Center each line of the figlet text
                    start_x = max(0, (max_x - len(line)) // 2)
                    self.screen.addstr(title_y + i, start_x, line, curses.color_pair(1))

            with_zeynep_text = "-- With Zeynep --"
            with_zeynep_y = title_y + len(title_lines)  # Position right after title
            with_zeynep_x = max(0, (max_x - len(with_zeynep_text)) // 2)  # Center text
            self.screen.addstr(with_zeynep_y, with_zeynep_x, with_zeynep_text, curses.color_pair(1))

            menu_start_y = with_zeynep_y + 2  # +2 for spacing

            menu_start_x = max(0, (max_x - BOX_WIDTH) // 2)


            # Draw menu items with box
            menu_items = [
                "┌" + "─" * (BOX_WIDTH - 2) + "┐",
                "│" + self._center_text("♠ ♥ ♣ ♦", BOX_WIDTH - 2) + "│",
                "│" + " " * (BOX_WIDTH - 2) + "│",
                "│" + self._center_text("[N] NEW GAME", BOX_WIDTH - 2) + "│",
                "│" + self._center_text("[Q] QUIT", BOX_WIDTH - 2) + "│",
                "│" + self._center_text(f"[D] DIFFICULTY: {current_difficulty.name}", BOX_WIDTH - 2) + "│",
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
                return (True, current_difficulty)  # Return tuple with both values
            elif key in (ord('q'), ord('Q')):
                return (False, current_difficulty)  # Return tuple with both values
            elif key in (ord('d'), ord('D')):
                # Cycle through difficulties
                if current_difficulty == Difficulty.EASY:
                    current_difficulty = Difficulty.MEDIUM
                elif current_difficulty == Difficulty.MEDIUM:
                    current_difficulty = Difficulty.HARD
                else:
                    current_difficulty = Difficulty.EASY

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
        menu_result = self._show_main_menu()
        should_continue, difficulty = menu_result
        if not should_continue:
            return

        self.sounds.start_music()

        while True:
            if not self.new_game(difficulty):
                self.sounds.stop_music()
                return

            game_running = True
            while game_running:
                self._draw_screen()
                if not self._handle_input():
                    return

                if self._check_win():
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

            # Constants for layout
            CARD_WIDTH = 4  # [A♠]
            CARD_SPACING = 2
            TABLEAU_COLUMNS = 7
            TOP_MARGIN = 2

            # Calculate layout
            usable_width = max_x - 4  # 2 char margin on each side
            column_width = CARD_WIDTH + CARD_SPACING
            left_margin = (usable_width - (column_width * TABLEAU_COLUMNS)) // 2 + 2

            # Draw header (bank and controls)
            current_y = 1
            header = f"Bank: ${self.bank}   [Q:Quit, N:New Game, "
            hint_text = "C:Call Zeynep(-7$)"
            if self.hint_highlighted:
                self.screen.addstr(current_y, left_margin, header)
                self.screen.addstr(hint_text, curses.A_REVERSE | curses.color_pair(3))
                self.screen.addstr("]")
            else:
                self.screen.addstr(current_y, left_margin, header + hint_text + "]")

            # Draw message if exists
            if self.message:
                current_y += 1
                self.screen.addstr(current_y, left_margin, self.message, curses.color_pair(3))

            current_y = TOP_MARGIN + 2

            # Draw top row (stock, waste, foundations)
            # Stock pile
            stock_x = left_margin
            stock_str = "[##]" if self.stock else "[  ]"
            attrs = curses.A_REVERSE if (self.cursor['y'] == 0 and self.cursor['x'] == 0) else curses.A_NORMAL
            self.screen.addstr(current_y, stock_x, stock_str, attrs)

            # Waste pile
            waste_x = stock_x + column_width
            if self.waste:
                visible_waste = self.waste[-3:]  # Show up to 3 waste cards
                for i, card in enumerate(visible_waste):
                    card_x = waste_x + (i * 2)  # Overlap waste cards
                    attrs = curses.A_REVERSE if (self.cursor['y'] == 0 and
                                                 self.cursor['x'] == 1 and
                                                 i == len(visible_waste) - 1) else curses.A_NORMAL
                    color = curses.color_pair(1) if card.suit.color == 'red' else curses.A_NORMAL
                    self.screen.addstr(current_y, card_x, str(card), attrs | color)
            else:
                self.screen.addstr(current_y, waste_x, "[  ]")

            # Foundation piles
            foundation_x = left_margin + (column_width * 3)
            for i in range(4):
                card_x = foundation_x + (i * column_width)
                if i < len(self.foundation):
                    if self.foundation[i]:
                        card = self.foundation[i][-1]
                        attrs = curses.A_REVERSE if (self.cursor['y'] == 0 and
                                                     self.cursor['x'] == i + 2) else curses.A_NORMAL
                        color = curses.color_pair(1) if card.suit.color == 'red' else curses.A_NORMAL
                        self.screen.addstr(current_y, card_x, str(card), attrs | color)
                    else:
                        attrs = curses.A_REVERSE if (self.cursor['y'] == 0 and
                                                     self.cursor['x'] == i + 2) else curses.A_NORMAL
                        self.screen.addstr(current_y, card_x, "[  ]", attrs)

            # Draw tableau
            tableau_y = current_y + 2
            for i in range(TABLEAU_COLUMNS):
                pile_x = left_margin + (i * column_width)

                # Draw empty slot or cards
                if not self.tableau[i]:
                    attrs = curses.A_REVERSE if (self.cursor['y'] == 1 and
                                                 self.cursor['x'] == i) else curses.A_NORMAL
                    self.screen.addstr(tableau_y, pile_x, "[  ]", attrs)
                else:
                    for j, card in enumerate(self.tableau[i]):
                        if tableau_y + j >= max_y:
                            break

                        attrs = curses.A_NORMAL
                        if self.cursor['y'] == j + 1 and self.cursor['x'] == i:
                            attrs = curses.A_REVERSE
                        elif (self.selected and self.selected[0] == 'tableau' and
                              self.selected[1] == i and self.selected[2] <= j):
                            attrs = curses.A_REVERSE

                        color = curses.color_pair(1) if (card.face_up and
                                                         card.suit.color == 'red') else curses.A_NORMAL
                        self.screen.addstr(tableau_y + j, pile_x, str(card), attrs | color)

            # Draw debug info if enabled
            if self.debug_mode:
                self._draw_debug_info(tableau_y + max([len(pile) for pile in self.tableau]) + 2)

            self.screen.refresh()

        except Exception as e:
            self.logger.exception(f"Draw screen error: {str(e)}")

    def _draw_debug_info(self, start_y):
        """Helper method to draw debug information"""
        try:
            max_y, max_x = self.screen.getmaxyx()
            if start_y >= max_y - 5:
                return

            left_margin = 2
            self.screen.addstr(start_y, left_margin, "=" * (max_x - 4), curses.color_pair(3))
            start_y += 1

            # Basic game info
            self.screen.addstr(start_y, left_margin, "DEBUG MODE", curses.color_pair(3) | curses.A_BOLD)
            start_y += 1

            debug_lines = [
                f"Cursor: ({self.cursor['x']}, {self.cursor['y']})",
                f"Selected: {self.selected}",
                f"Stock: {len(self.stock)} cards",
                f"Waste: {len(self.waste)} cards"
            ]

            for line in debug_lines:
                if start_y >= max_y:
                    break
                self.screen.addstr(start_y, left_margin, line, curses.color_pair(3))
                start_y += 1

            # Foundation progress
            if start_y < max_y:
                progress = []
                for suit in Suit:
                    suit_height = 0
                    for pile in self.foundation:
                        if pile and pile[-1].suit == suit:
                            suit_height = pile[-1].rank.number
                    progress.append(f"{suit.symbol}:{suit_height}")
                self.screen.addstr(start_y, left_margin,
                                   f"Foundation Progress: {' '.join(progress)}",
                                   curses.color_pair(3))
                start_y += 1

            # Solvability status
            if start_y < max_y:
                if not hasattr(self, '_solvability_cache'):
                    self._solvability_cache = None
                    self._last_state_hash = None

                current_state = str(self.tableau) + str(self.foundation) + str(self.waste)
                current_hash = hash(current_state)

                if current_hash != self._last_state_hash:
                    self._solvability_cache = None
                    self._last_state_hash = current_hash

                if self._solvability_cache is None:
                    status = "NOT CALCULATED (press 'S' to calculate)"
                    color = curses.color_pair(3)
                else:
                    status = "SOLVABLE" if self._solvability_cache else "NOT SOLVABLE"
                    color = curses.color_pair(2) if self._solvability_cache else curses.color_pair(1)

                self.screen.addstr(start_y, left_margin, f"Game Status: {status}", color)
                start_y += 1

            # Available moves
            if start_y < max_y:
                moves = self._get_possible_moves()
                self.screen.addstr(start_y, left_margin,
                                   f"Available Moves: {len(moves)}",
                                   curses.color_pair(3))
                start_y += 1

                # Show up to 3 sample moves
                prioritized_moves = self._prioritize_moves(moves)
                for move in prioritized_moves[:5]:
                    if start_y >= max_y:
                        break
                    self.screen.addstr(start_y, left_margin + 2,
                                       f"→ {move[:max_x - left_margin - 4]}",
                                       curses.color_pair(2))
                    start_y += 1

        except Exception as e:
            self.logger.exception(f"Debug screen error: {str(e)}")


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

    def _handle_move(self, key):
        """Helper to detect if a valid move was made due to my previous stupid coding practices :3"""
        if key in [ord('q'), ord('n'), ord('d')]:
            return False

        if key == ord('c'):
            return True

        if key == ord(' '):
            if self.selected:
                return True

        if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            prev_x, prev_y = self.cursor['x'], self.cursor['y']
            # If cursor moved to a new valid position
            self._handle_cursor_movement(key)
            return (self.cursor['x'] != prev_x or self.cursor['y'] != prev_y)

        return False

    def _handle_input(self):
        try:
            key = self.screen.getch()

            # Handle move and timer updates
            if key in [ord('q')]:
                return False
            elif key == ord('n'):
                return self.new_game()
            elif key == ord('d'):
                self.debug_mode = not self.debug_mode
                self._debug_print("Debug mode toggled")
                return True
            elif key == ord('m'):
                # Toggle music on/off
                if pygame.mixer.music.get_volume() > 0:
                    pygame.mixer.music.set_volume(0)
                    self.message = "music off :("
                else:
                    pygame.mixer.music.set_volume(0.2)  # Default volume
                    self.message = "music on :)"
                self.message_timer = time.time()  # Set the timer when message is updated

            elif key in [ord('s')]:
                if self.debug_mode and self._solvability_cache is None:
                    start_time = time.time()
                    self._solvability_cache = self._is_game_solvable()
                    elapsed = time.time() - start_time
                    self.message = f"Calculation took {elapsed:.3f}s"
                    self.message_timer = time.time()


            elif key == ord('c'):
                self._show_hint()
                return True
            elif key == ord(' '):
                try:
                    if not self._handle_selection():
                        self.selected = None  # Reset selection on invalid move
                except Exception as e:
                    self.logger.exception(f"Selection error: {str(e)}")
            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                # Store previous position for move detection
                prev_x, prev_y = self.cursor['x'], self.cursor['y']
                self._handle_cursor_movement(key)
                # Check if cursor actually moved
                if (self.cursor['x'] != prev_x or self.cursor['y'] != prev_y):
                    self.last_move_time = time.time()
                    self.hint_highlighted = False
                    self.stuck_timer_started = False

            # Check stuck timers
            current_time = time.time()
            time_since_move = current_time - self.last_move_time

            if not self.stuck_timer_started and time_since_move >= 180:  # 3 minutes
                self.hint_highlighted = True
                self.stuck_timer_started = True

            if time_since_move >= 360:  # 6 minutes
                self._show_hint()  # Show free hint
                self.last_move_time = current_time  # Reset timer
                self.hint_highlighted = False
                self.stuck_timer_started = False

            return True
        except Exception as e:
            self.logger.exception(f"Input handling error: {str(e)}")
            return True

    def _handle_cursor_movement(self, key):
        """Helper to handle cursor movement"""
        if key == curses.KEY_UP and self.cursor['y'] > 0:
            if self.cursor['y'] == 1:
                if self.cursor['x'] <= 1:
                    self.cursor['x'] = min(self.cursor['x'], 1)
                else:
                    self.cursor['x'] = min(self.cursor['x'] - 1, 5)
            self.cursor['y'] -= 1
        elif key == curses.KEY_DOWN:
            max_y = max(len(pile) for pile in self.tableau)
            if self.cursor['y'] == 0:
                if self.cursor['x'] <= 1:
                    self.cursor['x'] = min(self.cursor['x'], 1)
                else:
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
            else:
                # Trigger game over only when clicking empty stock
                if not self._has_valid_moves():
                    self.sounds.play_game_over()
                    return False
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

    def _is_game_solvable(self) -> bool:
        """
        Solvability checker that considers one-pass stock restriction.
        """

        def get_all_cards():
            """Map every card to its location and what's above it"""
            card_info = {}

            # First, calculate actual card accessibility from stock/waste
            # Cards in stock can only be accessed in their current order, once
            stock_waste_sequence = []
            # First add remaining stock cards in order
            stock_waste_sequence.extend(self.stock)
            # Then add waste cards in reverse order (top card first)
            stock_waste_sequence.extend(reversed(self.waste))

            # Process stock cards - they can only be accessed in sequence
            for i, card in enumerate(self.stock):
                card_info[(card.suit, card.rank)] = {
                    'location': 'stock',
                    'pile': 0,
                    'position': i,
                    'face_up': False,
                    'cards_above': [],
                    'access_order': i  # Lower means accessed sooner
                }

            # Process waste cards - they're already turned over
            for i, card in enumerate(reversed(self.waste)):
                card_info[(card.suit, card.rank)] = {
                    'location': 'waste',
                    'pile': 0,
                    'position': i,
                    'face_up': True,
                    'cards_above': [],
                    'access_order': len(self.stock) + i  # Continue numbering after stock
                }

            # Process tableau piles
            for pile_idx, pile in enumerate(self.tableau):
                for card_idx, card in enumerate(pile):
                    cards_above = pile[card_idx + 1:]
                    card_info[(card.suit, card.rank)] = {
                        'location': 'tableau',
                        'pile': pile_idx,
                        'position': card_idx,
                        'face_up': card.face_up,
                        'cards_above': cards_above,
                        'access_order': None  # Tableau cards don't have fixed access order
                    }

            # Process foundation
            for pile_idx, pile in enumerate(self.foundation):
                for card_idx, card in enumerate(pile):
                    card_info[(card.suit, card.rank)] = {
                        'location': 'foundation',
                        'pile': pile_idx,
                        'position': card_idx,
                        'face_up': True,
                        'cards_above': [],
                        'access_order': -1  # Already played
                    }

            self.logger.info("=== Current Game State ===")
            self.logger.info(f"Stock cards remaining: {len(self.stock)}")
            self.logger.info(f"Waste cards: {len(self.waste)}")
            self.logger.info("\nCard Locations:")
            for (suit, rank), info in card_info.items():
                access_info = f"access #{info['access_order']}" if info['access_order'] is not None else "tableau"
                self.logger.info(
                    f"[{rank.symbol}{suit.symbol}]: {info['location']} "
                    f"pile {info['pile']}, position {info['position']} "
                    f"({'face up' if info['face_up'] else 'hidden'}) - {access_info}"
                )

            return card_info

        def is_card_accessible(card_key, target_access_order, card_info):
            """
            Check if a card can be accessed when needed.
            target_access_order represents when we need the card.
            """
            info = card_info[card_key]

            if info['location'] == 'foundation':
                return False  # Already in foundation

            if info['location'] in ['stock', 'waste']:
                # Card must be accessible before we need it
                if info['access_order'] is not None and info['access_order'] > target_access_order:
                    return False
                return True

            # For tableau cards
            if info['location'] == 'tableau':
                if not info['face_up']:
                    # For face-down cards, check if cards above can be moved
                    for card_above in info['cards_above']:
                        above_key = (card_above.suit, card_above.rank)
                        if not is_card_accessible(above_key, target_access_order, card_info):
                            return False
                return True

            return False

        def check_suit_buildable(suit, card_info):
            """Check if a suit can be built considering one-pass restriction"""
            self.logger.info(f"\nAnalyzing {suit.symbol} suit buildability:")

            # Get all cards of this suit
            suit_cards = [(rank, info) for (s, rank), info in card_info.items() if s == suit]
            suit_cards.sort(key=lambda x: x[0].number)  # Sort by rank

            if len(suit_cards) != 13:
                self.logger.error(f"{suit.symbol} suit: Missing cards! Found {len(suit_cards)}/13")
                return False

            current_target_order = 0  # Increases as we need later cards

            # Check accessibility for each card in order
            for rank, info in suit_cards:
                card_key = (suit, rank)
                location = info['location']
                access_order = info['access_order']

                self.logger.info(
                    f"Checking [{rank.symbol}{suit.symbol}] in {location} "
                    f"(access order: {access_order if access_order is not None else 'tableau'})"
                )

                if not is_card_accessible(card_key, current_target_order, card_info):
                    if info['location'] in ['stock', 'waste']:
                        self.logger.error(
                            f"{suit.symbol} suit: [{rank.symbol}{suit.symbol}] will be accessible "
                            f"too late (access #{access_order}, needed by #{current_target_order})"
                        )
                    else:
                        cards_above = [f"{c.rank.symbol}{c.suit.symbol}" for c in info['cards_above']]
                        self.logger.error(
                            f"{suit.symbol} suit: [{rank.symbol}{suit.symbol}] is blocked in tableau. "
                            f"Cards above: {', '.join(cards_above) if cards_above else 'none'}"
                        )
                    return False

                current_target_order += 1

            return True

        # Main check logic
        try:
            self.logger.info("\n=== Starting Solvability Check (One-Pass Rule) ===")

            card_info = get_all_cards()

            for suit in Suit:
                if not check_suit_buildable(suit, card_info):
                    self.logger.info("Game is NOT solvable - sequence or timing issues detected")
                    return False

            self.logger.info("\nGame is SOLVABLE - all suits can be built within one pass!")
            return True

        except Exception as e:
            self.logger.error(f"Error in solvability checker: {str(e)}")
            return False


    def _create_game_state(self) -> tuple:
        """Create hashable game state representation"""
        # Convert tableau to immutable structure
        tableau_state = []
        for pile in self.tableau:
            pile_state = []
            for card in pile:
                # Include face_up status in card state
                card_state = (card.suit, card.rank, card.face_up)
                pile_state.append(card_state)
            tableau_state.append(tuple(pile_state))

        # Convert foundation to immutable structure
        foundation_state = []
        for pile in self.foundation:
            pile_state = []
            for card in pile:
                # Foundation cards are always face up
                card_state = (card.suit, card.rank, True)
                pile_state.append(card_state)
            foundation_state.append(tuple(pile_state))

        # Convert stock and waste, including face_up status
        stock_state = tuple((card.suit, card.rank, False) for card in self.stock)
        waste_state = tuple((card.suit, card.rank, True) for card in self.waste)

        return (tuple(tableau_state), tuple(foundation_state), stock_state, waste_state)

    def _can_solve_state(self, state, memo: set, max_depth: int, progress_callback=None, depth_callback=None) -> bool:
        """Recursive state solver with memoization"""
        try:
            if max_depth <= 0:
                return False

            if depth_callback:
                depth_callback(max_depth)

            if progress_callback:
                if not progress_callback():
                    return False

            # Check if we've seen this state
            state_hash = hash(state)
            if state_hash in memo:
                return False
            memo.add(state_hash)

            tableau_state, foundation_state, stock_state, waste_state = state

            # Win condition: all foundations complete
            if all(len(pile) == 13 for pile in foundation_state):
                return True

            # Get all possible moves from current state
            possible_moves = self._get_state_moves(state)

            # Try each move
            for move in possible_moves:
                new_state = self._apply_move_to_state(state, move)
                if new_state != state:  # Only recurse if state changed
                    if self._can_solve_state(new_state, memo, max_depth - 1):
                        return True

            return False

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error in _can_solve_state: {str(e)}", exc_info=True)
            return False

    def _apply_move_to_state(self, state, move) -> tuple:
        """Apply a move to a state and return new state"""
        tableau_state, foundation_state, stock_state, waste_state = state

        try:
            move_type, source, dest = move

            # Convert to lists for manipulation
            waste_state = list(waste_state)
            stock_state = list(stock_state)
            tableau_state = [list(pile) for pile in tableau_state]
            foundation_state = [list(pile) for pile in foundation_state]

            if move_type == 'waste_to_foundation':
                # Move card from waste to foundation
                card = waste_state.pop()
                foundation_state[dest].append(card)

            elif move_type == 'waste_to_tableau':
                # Move card from waste to tableau
                card = waste_state.pop()
                tableau_state[dest].append(card)

            elif move_type == 'tableau_to_foundation':
                # Move card from tableau to foundation
                source_pile, card_idx = source
                card = tableau_state[source_pile][card_idx]
                tableau_state[source_pile] = tableau_state[source_pile][:card_idx]
                foundation_state[dest].append(card)

            elif move_type == 'tableau_to_tableau':
                # Move cards from one tableau pile to another
                source_pile, card_idx = source
                cards = tableau_state[source_pile][card_idx:]
                tableau_state[source_pile] = tableau_state[source_pile][:card_idx]
                tableau_state[dest].extend(cards)

            elif move_type == 'stock_to_waste':
                # Move top card from stock to waste
                if stock_state:
                    card = stock_state.pop(0)
                    waste_state.append(card)

            # Convert everything back to tuples
            new_tableau = tuple(tuple(pile) for pile in tableau_state)
            new_foundation = tuple(tuple(pile) for pile in foundation_state)
            new_stock = tuple(stock_state)
            new_waste = tuple(waste_state)

            return (new_tableau, new_foundation, new_stock, new_waste)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error in _apply_move_to_state: {str(e)}", exc_info=True)
            return state  # Return original state if there's an error

    def _get_state_moves(self, state) -> List[tuple]:
        """Get all possible moves from a state"""
        tableau_state, foundation_state, stock_state, waste_state = state
        moves = []

        try:
            # Check waste to foundation/tableau moves
            if waste_state:
                top_waste = waste_state[-1]

                # To foundation
                for i, foundation in enumerate(foundation_state):
                    if not foundation and top_waste[1] == Rank.ACE:
                        moves.append(('waste_to_foundation', None, i))
                    elif (foundation and
                          top_waste[0] == foundation[-1][0] and  # Same suit
                          top_waste[1].number == foundation[-1][1].number + 1):  # Next rank
                        moves.append(('waste_to_foundation', None, i))

                # To tableau
                for i, pile in enumerate(tableau_state):
                    if not pile and top_waste[1] == Rank.KING:
                        moves.append(('waste_to_tableau', None, i))
                    elif pile:  # Check if pile exists and has cards
                        top_tableau = pile[-1]
                        if (top_tableau[2] and  # Target card is face up
                                top_waste[0].color != top_tableau[0].color and  # Alternate colors
                                top_waste[1].number == top_tableau[1].number - 1):  # Descending order
                            moves.append(('waste_to_tableau', None, i))

            # Stock to waste move
            if stock_state:
                moves.append(('stock_to_waste', None, None))

            # Check tableau to foundation/tableau moves
            for i, source_pile in enumerate(tableau_state):
                if not source_pile:
                    continue

                # Find first face-up card
                for j, card_info in enumerate(source_pile):
                    if not card_info[2]:  # Skip face-down cards
                        continue

                    # To foundation
                    suit, rank, _ = card_info
                    for k, foundation in enumerate(foundation_state):
                        if not foundation and rank == Rank.ACE:
                            moves.append(('tableau_to_foundation', (i, j), k))
                        elif (foundation and
                              suit == foundation[-1][0] and
                              rank.number == foundation[-1][1].number + 1):
                            moves.append(('tableau_to_foundation', (i, j), k))

                    # To other tableau piles
                    for k, target_pile in enumerate(tableau_state):
                        if k != i:  # Don't move to same pile
                            if not target_pile and rank == Rank.KING:
                                moves.append(('tableau_to_tableau', (i, j), k))
                            elif target_pile:
                                top_target = target_pile[-1]
                                if (top_target[2] and  # Target is face up
                                        suit.color != top_target[0].color and
                                        rank.number == top_target[1].number - 1):
                                    moves.append(('tableau_to_tableau', (i, j), k))

            return moves

        except Exception as e:
            self.logger.error(f"Error in _get_state_moves: {str(e)}")
            return []

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

    def _can_place_on_foundation(self, card, foundation) -> bool:
        """Check if card can be placed on foundation"""
        if not foundation:
            return card[1] == Rank.ACE
        top_card = foundation[-1]
        return (card[0] == top_card[0] and  # Same suit
                card[1].number == top_card[1].number + 1)  # Next rank

    def _can_place_on_tableau(self, card, tableau_pile) -> bool:
        """Check if card can be placed on tableau pile"""
        if not tableau_pile:
            return card[1] == Rank.KING
        top_card = tableau_pile[-1]
        return (card[0].color != top_card[0].color and  # Alternate colors
                card[1].number == top_card[1].number - 1)  # Previous rank

    def _check_win(self):
        if all(len(pile) == 13 for pile in self.foundation):
            bonus = 100
            self.bank += bonus
            self.message = f"You won! Bank: ${self.bank} (Bonus: +${bonus})"
            self.sounds.play_game_win()
            return True
        return False

    def _check_game_over(self): return False

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
        self.bank -= 7
        moves = self._get_possible_moves()
        if moves:
            # Sort moves by priority
            prioritized_moves = self._prioritize_moves(moves)
            self.message = f"Zeynep: {prioritized_moves[0]}"
            self.logger.debug(f"Hint provided: {prioritized_moves[0]}")
        else:
            n = random.randint(1, 5)
            if n == 1:
                self.message = "Zeynep: We gotta draw now... No moves left!"
            elif n == 2:
                self.message = "Zeynep: I'm not sure about this one... Draw a card!"
            elif n == 3:
                self.message = "Zeynep: I think you're stuck... Draw a card!"
            elif n == 4:
                self.message = "Zeynep: I'm out of ideas... Draw a card!"
            else:
                self.message = "Zeynep: I'm stumped... Draw a card!"

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
    curses.curs_set(1)  # Hide cursor
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
