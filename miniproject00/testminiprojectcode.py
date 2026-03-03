# ...existing code...

import random

def create_deck(shuffle=True):
    ranks = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    suits = ['♠','♥','♦','♣']
    deck = [(r,s) for r in ranks for s in suits]
    if shuffle:
        random.shuffle(deck)
    return deck

def deal_card(deck):
    if not deck:
        deck.extend(create_deck())  # reshuffle if empty
        random.shuffle(deck)
    return deck.pop()

def card_value(rank):
    if rank in ['J','Q','K']:
        return 10
    if rank == 'A':
        return 11  # simple handling; adjust for soft/hard aces as needed
    return int(rank)

# ...existing code...

# replace your random.randint draws with deck dealing:
deck = create_deck()
player_hand = [deal_card(deck), deal_card(deck)]
dealer_hand = [deal_card(deck), deal_card(deck)]

player_total = sum(card_value(r) for r,_ in player_hand)
dealer_total = sum(card_value(r) for r,_ in dealer_hand)

print("You drew:", player_hand, "=>", player_total)
print("Dealer shows:", dealer_hand[0], "=>", card_value(dealer_hand[0][0]))

# ...existing code...