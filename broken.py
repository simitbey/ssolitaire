import curses
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
import time


class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'

    @property
    def color(self):
        return curses.COLOR_RED if self in [Suit.HEARTS, Suit.DIAMONDS] else curses.COLOR_BLACK


class Card:
    def __init__(self, suit: Suit, value: int, face_up: bool = False):
        self.suit = suit
        self.value = value
        self.face_up = face_up

    @property
    def color(self):
        return self.suit.color

    def __str__(self):
        values = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        value_str = values.get(self.value, str(self.value))
        if self.face_up:
            return f"{value_str}{self.suit.value}"
        return "🂠"


class Pile:
    def __init__(self, x: int, y: int, name: str):
        self.cards: List[Card] = []
        self.x = x
        self.y = y
        self.name = name
        self.selected = False

    def add_card(self, card: Card):
        self.cards.append(card)

    def remove_card(self) -> Optional[Card]:
        if self.cards:
            return self.cards.pop()
        return None


class VegasSolitaire:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
        self.money = 0
        self.current_game_cost = -52
        self.card_value = 5
        self.generate_winnable_game()

    def setup_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    def generate_winnable_game(self):
        while True:
            self.initialize_game_state()
            if self.is_winnable():
                break

    def initialize_game_state(self):
        # Similar to previous initialize_game but with tracking
        self.stock = Pile(0, 0, "Stock")
        self.waste = Pile(10, 0, "Waste")
        self.foundations = [Pile(30 + i * 10, 0, f"F{i}") for i in range(4)]
        self.tableau = [Pile(i * 10, 5, f"T{i}") for i in range(7)]

        # Create deck
        deck = []
        for suit in Suit:
            for value in range(1, 14):
                deck.append(Card(suit, value))

        # Before shuffling, we'll try different configurations
        self.try_winnable_configuration(deck)

    def try_winnable_configuration(self, deck):
        """Uses reverse-engineering approach to ensure winnability"""
        found_winnable = False
        max_attempts = 1000  # Prevent infinite loops

        while not found_winnable and max_attempts > 0:
            temp_deck = deck.copy()
            random.shuffle(temp_deck)

            # Deal cards to tableau
            tableau_cards = []
            for i in range(7):
                tableau_cards.extend(temp_deck[:i + 1])
                temp_deck = temp_deck[i + 1:]

            # Remaining cards go to stock
            stock_cards = temp_deck

            # Simulate play to check winnability
            if self.simulate_game(tableau_cards.copy(), stock_cards.copy()):
                found_winnable = True
                # Actually deal the cards now
                self.deal_cards(deck, tableau_cards, stock_cards)

            max_attempts -= 1

    def simulate_game(self, tableau_cards, stock_cards) -> bool:
        """
        Simulates the game to check if it's winnable
        Returns True if game can be won in one pass through stock
        """
        # Create simulation state
        sim_foundations = [[] for _ in range(4)]
        sim_tableau = [[] for _ in range(7)]
        sim_stock = stock_cards.copy()
        sim_waste = []

        # Setup initial tableau
        card_index = 0
        for i in range(7):
            for j in range(i + 1):
                sim_tableau[i].append(tableau_cards[card_index])
                card_index += 1

        # Simulate gameplay
        moves_possible = True
        stock_passes = 0

        while moves_possible and stock_passes < 1:
            moves_possible = False

            # Try all possible moves
            # 1. Check for direct foundation moves
            for tab in sim_tableau:
                if tab and self.can_move_to_foundation_sim(tab[-1], sim_foundations):
                    moves_possible = True
                    self.move_to_foundation_sim(tab, sim_foundations)

            # 2. Check waste to foundation
            if sim_waste and self.can_move_to_foundation_sim(sim_waste[-1], sim_foundations):
                moves_possible = True
                self.move_to_foundation_sim(sim_waste, sim_foundations)

            # 3. Try tableau to tableau moves
            for i, source in enumerate(sim_tableau):
                if not source:
                    continue
                for j, target in enumerate(sim_tableau):
                    if i != j and self.can_move_to_tableau_sim(source[-1], target):
                        moves_possible = True
                        self.move_cards_sim(source, target)

            # 4. Deal from stock if no moves possible
            if not moves_possible and sim_stock:
                moves_possible = True
                card = sim_stock.pop(0)
                sim_waste.append(card)
            elif not moves_possible and not sim_stock:
                stock_passes += 1

        # Check if all cards are in foundation
        total_foundation_cards = sum(len(f) for f in sim_foundations)
        return total_foundation_cards == 52

    def deal_cards(self, deck, tableau_cards, stock_cards):
        """Actually deals the cards in the winning configuration"""
        # Deal to tableau
        card_index = 0
        for i, pile in enumerate(self.tableau):
            for j in range(i + 1):
                card = tableau_cards[card_index]
                card.face_up = (j == i)  # Only last card face up
                pile.add_card(card)
                card_index += 1

        # Deal to stock
        for card in stock_cards:
            card.face_up = False
            self.stock.add_card(card)

    def initialize_game(self):
        self.stock = Pile(0, 0, "Stock")
        self.waste = Pile(10, 0, "Waste")
        self.foundations = [Pile(30 + i * 10, 0, f"F{i}") for i in range(4)]
        self.tableau = [Pile(i * 10, 5, f"T{i}") for i in range(7)]

        # Create and shuffle deck
        deck = []
        for suit in Suit:
            for value in range(1, 14):
                deck.append(Card(suit, value))
        random.shuffle(deck)

        # Deal cards to tableau
        for i, pile in enumerate(self.tableau):
            for j in range(i + 1):
                card = deck.pop()
                if j == i:  # Last card in pile
                    card.face_up = True
                pile.add_card(card)

        # Remaining cards go to stock
        for card in deck:
            self.stock.add_card(card)

        self.selected_pile = None
        self.selected_card_index = None
        self.cursor_x = 0
        self.cursor_y = 0

    def draw(self):
        self.stdscr.clear()

        # Draw money information
        self.stdscr.addstr(0, 50, f"Money: ${self.money:.2f}", curses.color_pair(3))
        self.stdscr.addstr(1, 50, f"Current Game: ${self.current_game_cost:.2f}",
                           curses.color_pair(1) if self.current_game_cost < 0 else curses.color_pair(3))

        # Draw stock
        stock_display = f"[{len(self.stock.cards)}]" if self.stock.cards else "[ ]"
        self.stdscr.addstr(self.stock.y, self.stock.x, stock_display)

        # Draw waste
        if self.waste.cards:
            card = self.waste.cards[-1]
            self.draw_card(self.waste.y, self.waste.x, card)

        # Draw foundations
        for foundation in self.foundations:
            if foundation.cards:
                self.draw_card(foundation.y, foundation.x, foundation.cards[-1])
            else:
                self.stdscr.addstr(foundation.y, foundation.x, "[ ]")

        # Draw tableau
        for pile in self.tableau:
            for i, card in enumerate(pile.cards):
                self.draw_card(pile.y + i, pile.x, card)

        # Draw cursor
        self.stdscr.addstr(self.cursor_y, self.cursor_x, ">>")

        self.stdscr.refresh()

    def draw_card(self, y: int, x: int, card: Card):
        if not card.face_up:
            self.stdscr.addstr(y, x, str(card))
            return

        color = curses.color_pair(1) if card.color == curses.COLOR_RED else curses.color_pair(0)
        if self.selected_pile and card in self.selected_pile.cards:
            color |= curses.A_REVERSE

        self.stdscr.addstr(y, x, str(card), color)

    def handle_input(self, key):
        if self.stock_exhausted:
            if key == ord('n'):
                self.generate_winnable_game()
                self.stock_exhausted = False
                return True
            elif key == ord('q'):
                return False
            return True
        if key == curses.KEY_LEFT:
            self.cursor_x = max(0, self.cursor_x - 10)
        elif key == curses.KEY_RIGHT:
            self.cursor_x = min(60, self.cursor_x + 10)
        elif key == curses.KEY_UP:
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == curses.KEY_DOWN:
            self.cursor_y = min(20, self.cursor_y + 1)
        elif key in [ord(' '), ord('\n')]:
            self.handle_selection()
        elif key == ord('r'):
            self.deal_from_stock()
        elif key == ord('q'):
            return False
        return True

    def handle_selection(self):
        # Find which pile was selected based on cursor position
        selected = None

        # Check stock
        if self.cursor_x == self.stock.x and self.cursor_y == self.stock.y:
            self.deal_from_stock()
            return

        # Check waste
        if self.cursor_x == self.waste.x and self.cursor_y == self.waste.y:
            selected = self.waste

        # Check foundations
        for foundation in self.foundations:
            if self.cursor_x == foundation.x and self.cursor_y == foundation.y:
                selected = foundation

        # Check tableau
        for pile in self.tableau:
            if self.cursor_x == pile.x and self.cursor_y >= pile.y:
                card_index = self.cursor_y - pile.y
                if card_index < len(pile.cards):
                    selected = pile
                    self.selected_card_index = card_index

        if selected:
            if self.selected_pile:
                self.try_move(self.selected_pile, selected)
                self.selected_pile = None
                self.selected_card_index = None
            else:
                self.selected_pile = selected

    def try_move(self, from_pile: Pile, to_pile: Pile):
        if not from_pile.cards or not from_pile.cards[-1].face_up:
            return False

        card = from_pile.cards[-1]

        # Moving to foundation
        if to_pile in self.foundations:
            if self.can_move_to_foundation(card, to_pile):
                to_pile.add_card(from_pile.remove_card())
                self.current_game_cost += self.card_value
                return True

        # Moving to tableau
        if to_pile in self.tableau:
            if self.can_move_to_tableau(card, to_pile):
                to_pile.add_card(from_pile.remove_card())
                return True

        return False

    def can_move_to_foundation(self, card: Card, foundation: Pile) -> bool:
        if not foundation.cards:
            return card.value == 1
        top_card = foundation.cards[-1]
        return (card.suit == top_card.suit and card.value == top_card.value + 1)

    def can_move_to_tableau(self, card: Card, tableau: Pile) -> bool:
        if not tableau.cards:
            return card.value == 13
        top_card = tableau.cards[-1]
        return (card.color != top_card.color and card.value == top_card.value - 1)

    def deal_from_stock(self):
        """Modified to implement one-pass rule"""
        if not self.stock.cards:
            self.stock_exhausted = True
            self.end_game()
            return

        card = self.stock.remove_card()
        if card:
            card.face_up = True
            self.waste.add_card(card)

    def run(self):
        running = True
        while running:
            self.draw()
            key = self.stdscr.getch()
            running = self.handle_input(key)

    def end_game(self):
        """Called when stock is exhausted"""
        # Calculate final score
        cards_in_foundation = sum(len(f.cards) for f in self.foundations)
        final_score = (cards_in_foundation * self.card_value) - 52
        self.money += final_score

        # Show end game message
        self.stdscr.addstr(10, 20, f"Game Over! Final Score: ${final_score}")
        self.stdscr.addstr(11, 20, f"Total Money: ${self.money}")
        self.stdscr.addstr(12, 20, "Press 'N' for new game or 'Q' to quit")
        self.stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)  # Hide cursor
    game = VegasSolitaire(stdscr)
    game.run()


if __name__ == "__main__":
    curses.wrapper(main)
