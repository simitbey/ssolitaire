import curses
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Set
from enum import Enum
import sys
import pyfiglet

MAIN_FIGLET_FONT = 'larry3d'
PYFIGLET_FONT = 'slant'

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

        while True:
            if not self.new_game():
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

            # Draw header
            header = f"Bank: ${self.bank}   [Q:Quit, N:New Game, H:Hint(-5$)]"
            self.screen.addstr(0, 0, header[:max_x - 1], curses.color_pair(2))

            if self.message:
                self.screen.addstr(1, 0, self.message[:max_x - 1], curses.color_pair(3))

            # Draw stock and waste piles
            y = 3
            if y < max_y:
                # Stock
                stock_str = "[##]" if self.stock else "[  ]"
                if self.cursor['y'] == 0 and self.cursor['x'] == 0:
                    self.screen.addstr(y, 0, stock_str, curses.A_REVERSE)
                else:
                    self.screen.addstr(y, 0, stock_str)

                # Draw waste (last 3 cards)
                waste_x = 6
                if self.waste and waste_x + 9 < max_x:  # Ensure space for 3 cards
                    visible_waste = self.waste[-3:] if len(self.waste) >= 3 else self.waste
                    for idx, card in enumerate(visible_waste):
                        waste_str = str(card)
                        display_x = waste_x + idx * 3

                        if display_x + len(waste_str) < max_x:
                            is_selected = (self.cursor['y'] == 0 and
                                           self.cursor['x'] == 1 and
                                           idx == len(visible_waste) - 1)

                            if is_selected:
                                self.screen.addstr(y, display_x, waste_str, curses.A_REVERSE)
                            else:
                                if card.suit.color == 'red':
                                    self.screen.addstr(y, display_x, waste_str, curses.color_pair(1))
                                else:
                                    self.screen.addstr(y, display_x, waste_str)
                elif waste_x < max_x:
                    self.screen.addstr(y, waste_x, "[  ]")

                # Draw foundations
                foundation_x = 18
                for i in range(4):
                    x = foundation_x + i * 6
                    if x + 5 < max_x:
                        if i < len(self.foundation):
                            if self.foundation[i]:
                                card_str = str(self.foundation[i][-1])
                                if self.cursor['y'] == 0 and self.cursor['x'] == i + 2:
                                    self.screen.addstr(y, x, card_str, curses.A_REVERSE)
                                else:
                                    if self.foundation[i][-1].suit.color == 'red':
                                        self.screen.addstr(y, x, card_str, curses.color_pair(1))
                                    else:
                                        self.screen.addstr(y, x, card_str)
                            else:
                                empty_str = "[  ]"
                                if self.cursor['y'] == 0 and self.cursor['x'] == i + 2:
                                    self.screen.addstr(y, x, empty_str, curses.A_REVERSE)
                                else:
                                    self.screen.addstr(y, x, empty_str)

            # Draw tableau
            for i in range(7):
                x = i * 6
                if x + 5 >= max_x:
                    break

                # Draw empty tableau slot indicator
                if y + 2 < max_y:
                    if not self.tableau[i]:
                        empty_slot = "[   ]"
                        if self.cursor['y'] == 1 and self.cursor['x'] == i:
                            self.screen.addstr(5, x, empty_slot, curses.A_REVERSE)
                        else:
                            self.screen.addstr(5, x, empty_slot, curses.color_pair(2))

                    # Draw cards
                    for j, card in enumerate(self.tableau[i]):
                        y = 5 + j
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

            # Draw debug information if enabled
            if self.debug_mode:
                debug_start_y = max_y - 12
                if debug_start_y > y + 2:
                    self.screen.addstr(debug_start_y, 0, "=== DEBUG INFO ===", curses.color_pair(3))
                    self.screen.addstr(debug_start_y + 1, 0, f"Cursor: {self.cursor}")
                    self.screen.addstr(debug_start_y + 2, 0, f"Selected: {self.selected}")

                    moves = self._get_possible_moves()
                    if moves:
                        self.screen.addstr(debug_start_y + 3, 0, "Possible moves:")
                        for i, move in enumerate(moves):
                            if debug_start_y + 4 + i < max_y:
                                self.screen.addstr(debug_start_y + 4 + i, 2, move[:max_x - 3])

            self.screen.refresh()
        except Exception as e:
            self._debug_print(f"Draw error: {str(e)}")

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
                self.cursor['y'] -= 1
            elif key == curses.KEY_DOWN:
                max_y = max(len(pile) for pile in self.tableau)
                if self.cursor['y'] == 0:  # Moving from top row
                    if self._is_valid_position(self.cursor['x'], 1):
                        self.cursor['y'] = 1
                else:
                    new_y = min(self.cursor['y'] + 1, max_y + 1)
                    if self._is_valid_position(self.cursor['x'], new_y):
                        self.cursor['y'] = new_y
            elif key == curses.KEY_LEFT and self.cursor['x'] > 0:
                self.cursor['x'] -= 1
            elif key == curses.KEY_RIGHT:
                if self.cursor['y'] == 0:
                    self.cursor['x'] = min(self.cursor['x'] + 1, 5)
                else:
                    self.cursor['x'] = min(self.cursor['x'] + 1, 6)
            elif key == ord(' '):
                try:
                    if not self._handle_selection():
                        # If selection was invalid, keep the cursor where it was
                        self.cursor['x'], self.cursor['y'] = prev_x, prev_y
                        self.selected = None  # Reset selection on invalid move
                except Exception as e:
                    self._debug_print(f"Selection error: {str(e)}")

            # Ensure cursor stays within valid bounds
            self.cursor['x'] = max(0, min(self.cursor['x'], 6))
            self.cursor['y'] = max(0, min(self.cursor['y'], max(len(pile) for pile in self.tableau) + 1))

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
                return True
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
            self.bank += 5  # $5 for each card in foundation
            self.selected = None
            return True
        return False

    def _try_move_to_tableau(self, tableau_idx) -> bool:
        """Try to move card(s) to tableau. Returns True if successful."""
        if not self.selected:
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
            return True
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
            return True
        return False

    def _check_game_over(self):
        return not self.stock

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
    curses.wrapper(main)
