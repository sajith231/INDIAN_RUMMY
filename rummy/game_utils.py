import random
import json

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
PRINTED_JOKERS_PER_DECK = 2
DECK_COUNT = 2


def generate_deck():
    """Generate a shuffled deck for Indian Rummy (2 decks + jokers)"""
    deck = []
    for deck_index in range(DECK_COUNT):
        deck.extend(f"{r}{s}" for s in SUITS for r in RANKS)
        for pj in range(PRINTED_JOKERS_PER_DECK):
            deck.append(f"JOKER{deck_index+1}-{pj+1}")
    random.shuffle(deck)
    return deck


def choose_wild_joker(deck):
    """Pick a random non-printed card to act as the wild joker"""
    for card in deck:
        if not card.startswith("JOKER"):
            return card
    return None


def is_printed_joker(card):
    return card.startswith("JOKER")


def deal_cards(deck, count=13):
    """Deal count cards from deck"""
    return deck[:count], deck[count:]


def to_json(data):
    """Convert data to JSON string"""
    return json.dumps(data)


def from_json(text):
    """Convert JSON string to data"""
    return json.loads(text) if text else []


def get_card_value(card):
    """Get numeric value of card for scoring"""
    if is_printed_joker(card):
        return 0
    rank = card[:-1]
    if rank in ['J', 'Q', 'K']:
        return 10
    elif rank == 'A':
        return 1
    else:
        return int(rank)


def get_card_rank_value(card):
    """Get rank value for sequence checking"""
    if is_printed_joker(card):
        return 0
    rank = card[:-1]
    values = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
              '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
    return values.get(rank, 0)


def get_card_suit(card):
    """Get suit of card"""
    if is_printed_joker(card):
        return None
    return card[-1]


# ---------- OLD SIMPLE CHECKS (still used anywhere else) ----------

def check_sequence(cards):
    """Check if cards form a valid sequence (min 3 cards), no jokers"""
    if any(is_printed_joker(c) for c in cards):
        return False
    if len(cards) < 3:
        return False
    
    # Sort by rank
    sorted_cards = sorted(cards, key=get_card_rank_value)
    
    # Check if all same suit
    suits = [get_card_suit(c) for c in sorted_cards]
    if len(set(suits)) != 1:
        return False
    
    # Check consecutive ranks
    ranks = [get_card_rank_value(c) for c in sorted_cards]
    for i in range(len(ranks) - 1):
        if ranks[i+1] - ranks[i] != 1:
            return False
    
    return True


def check_set(cards):
    """Check if cards form a valid set (same rank, different suits, min 3), no jokers"""
    if any(is_printed_joker(c) for c in cards):
        return False
    if len(cards) < 3:
        return False
    
    # Check all same rank
    ranks = [card[:-1] for card in cards]
    if len(set(ranks)) != 1:
        return False
    
    # Check all different suits
    suits = [get_card_suit(c) for c in cards]
    if len(set(suits)) != len(suits):
        return False
    
    return True


def calculate_hand_value(hand):
    """Calculate point value of hand"""
    return sum(get_card_value(card) for card in hand)


# ---------- NEW PROFESSIONAL RUMMY VALIDATION HELPERS ----------

def _is_joker(card, wild_joker):
    """Printed jokers + wild jokers"""
    if is_printed_joker(card):
        return True
    if not wild_joker:
        return False
    # Same rank as wild joker
    return card[:-1] == wild_joker[:-1]


def is_pure_sequence_group(cards, wild_joker):
    """
    Pure sequence:
    - Min 3 cards
    - Same suit
    - Consecutive
    - NO jokers (printed or wild)
    """
    if len(cards) < 3:
        return False
    if any(_is_joker(c, wild_joker) for c in cards):
        return False

    suits = [get_card_suit(c) for c in cards]
    if len(set(suits)) != 1:
        return False

    sorted_cards = sorted(cards, key=get_card_rank_value)
    ranks = [get_card_rank_value(c) for c in sorted_cards]
    for i in range(len(ranks) - 1):
        if ranks[i+1] - ranks[i] != 1:
            return False
    return True


def is_sequence_group(cards, wild_joker):
    """
    Normal sequence with jokers allowed.
    - Min 3
    - All non-joker cards same suit
    - After removing jokers, ranks must be consecutive with jokers filling gaps
    """
    if len(cards) < 3:
        return False

    non_jokers = [c for c in cards if not _is_joker(c, wild_joker)]
    joker_count = len(cards) - len(non_jokers)

    if not non_jokers:
        return False

    suits = [get_card_suit(c) for c in non_jokers]
    if len(set(suits)) != 1:
        return False

    sorted_cards = sorted(non_jokers, key=get_card_rank_value)
    ranks = [get_card_rank_value(c) for c in sorted_cards]

    gaps = 0
    for i in range(len(ranks) - 1):
        diff = ranks[i+1] - ranks[i] - 1
        if diff < 0:
            return False
        gaps += diff

    return gaps <= joker_count


def is_set_group(cards, wild_joker):
    """
    Set:
    - Min 3
    - All non-joker ranks same
    - Non-joker suits all different
    - Jokers can fill the rest
    """
    if len(cards) < 3:
        return False

    non_jokers = [c for c in cards if not _is_joker(c, wild_joker)]
    joker_count = len(cards) - len(non_jokers)

    if not non_jokers:
        # All jokers – allow as a set
        return True

    ranks = [c[:-1] for c in non_jokers]
    if len(set(ranks)) != 1:
        return False

    suits = [get_card_suit(c) for c in non_jokers]
    if len(suits) != len(set(suits)):
        return False

    # Jokers can always extend the set as extra suits
    return True


def validate_full_hand(groups, wild_joker):
    """
    Validate full 13-card rummy hand.

    Rules:
    - Use exactly 13 cards total
    - At least 1 pure sequence
    - At least 2 sequences in total (pure + normal)
    - All remaining groups must be valid sets or sequences
    """
    all_cards = []
    pure_count = 0
    seq_count = 0

    for group in groups:
        if not group:
            continue

        if is_pure_sequence_group(group, wild_joker):
            pure_count += 1
        elif is_sequence_group(group, wild_joker):
            seq_count += 1
        elif is_set_group(group, wild_joker):
            # valid set, no counter
            pass
        else:
            return False, "Invalid group found"

        all_cards.extend(group)

    if len(all_cards) != 13:
        return False, "You must use exactly 13 cards"

    if pure_count < 1:
        return False, "At least one pure sequence required"

    if pure_count + seq_count < 2:
        return False, "At least two sequences required"

    return True, "Valid hand"
