import random
import json

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']

def generate_deck():
    """Generate a shuffled deck of 52 cards"""
    deck = [f"{r}{s}" for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck

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
    rank = card[:-1]
    if rank in ['J', 'Q', 'K']:
        return 10
    elif rank == 'A':
        return 1
    else:
        return int(rank)

def get_card_rank_value(card):
    """Get rank value for sequence checking"""
    rank = card[:-1]
    values = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
              '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
    return values.get(rank, 0)

def get_card_suit(card):
    """Get suit of card"""
    return card[-1]

def check_sequence(cards):
    """Check if cards form a valid sequence (min 3 cards)"""
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
    """Check if cards form a valid set (same rank, different suits, min 3)"""
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
