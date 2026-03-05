
## This is the start of the app where we welcome the user and give them an option to deposit money and choose a game to play. 

print("Welcome to Cam's Crazy Casino!")
print("We offer games such as blackjack, roulette, and craps!")
choice_balance = input("How much would you like to deposit?")
balance = int(choice_balance)
choice = input("which game would you like to play?")

## Add a section that displays overall win percentage in each game and how much credit won/lost


#Blackjack Game ##USE RICH LIBRARY
import random
import time
from rich.console import Console
from rich.table import Table

console = Console()

def slow_print(lines, delay=0.4):
    for line in lines:
        console.print(line)
        time.sleep(delay)

def create_deck():
    ranks = [str(n) for n in range(2, 11)] + ["J", "Q", "K", "A"]
    suits = ["♠", "♥", "♦", "♣"]
    deck = [r + s for r in ranks for s in suits]
    random.shuffle(deck)
    return deck

def card_rank(card):
    return card[:-1]

def card_value(rank):
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)

def hand_value(cards):
    total = 0
    aces = 0
    for c in cards:
        r = card_rank(c)
        v = card_value(r)
        total += v
        if r == "A":
            aces += 1
    # convert A from 11 to 1 as needed
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def show_hand(title, cards, hide_first=False):
    table = Table(show_header=False, box=None)
    table.add_column()
    table.add_column(justify="right")
    if hide_first:
        table.add_row(title, f"[bold]{cards[0]}[/bold] + [grey42]??[/grey42]")
    else:
        for i, c in enumerate(cards):
            r = card_rank(c)
            v = "1/11" if r == "A" else str(card_value(r))
            table.add_row(title if i == 0 else "", f"{c}  ({v})")
    console.print(table)

if choice == "blackjack":
    slow_print(["Starting Blackjack...", "Good luck!"])
    while True:
        deck = create_deck()
        # bet
        try:
            bet = int(input("How much would you like to bet? "))
        except ValueError:
            console.print("[red]Please enter a whole number.[/red]")
            continue
        if bet <= 0:
            console.print("[red]Bet must be positive.[/red]")
            continue
        if bet > balance:
            console.print(f"[red]You only have ${balance}.[/red]")
            continue
        balance -= bet

        # initial deal
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        slow_print(["Dealing cards..."])
        show_hand("Player", player)
        console.print(f"Player total: {hand_value(player)}")
        show_hand("Dealer", dealer, hide_first=True)

        # immediate blackjack check
        if hand_value(player) == 21:
            console.print("[bold green]Blackjack! You win 1.5x your bet.[/bold green]")
            payout = int(bet * 1.5)
            balance += bet + payout
            console.print(f"New balance: {balance}")
        else:
            # player turn
            while True:
                action = input("Hit or stand? ").strip().lower()
                if action == "hit":
                    player.append(deck.pop())
                    show_hand("Player", player)
                    p_total = hand_value(player)
                    console.print(f"Player total: {p_total}")
                    if p_total > 21:
                        console.print("[red]Bust! You lose your bet.[/red]")
                        break
                elif action == "stand":
                    break
                else:
                    console.print("[yellow]Type 'hit' or 'stand'.[/yellow]")

            # dealer turn
            console.print("Dealer reveals hand:")
            show_hand("Dealer", dealer)
            while hand_value(dealer) < 17:
                time.sleep(0.6)
                dealer.append(deck.pop())
                console.print("Dealer hits:")
                show_hand("Dealer", dealer)
x

# Roulette Game

import random

playing = True

if choice == "roulette":
    print("Great choice! Let's play some roulette!")

#Just like blackjack, the while loop allows the user to play as many hands as they like until they want to stop. Randint and choice allows for random number and color selection.
while playing:

    choice_roulette_bet = input("how much would you like to bet?") 
    roulette_bet = int(choice_roulette_bet)
    print("Your remaining balance is $", balance - roulette_bet) #takes the balance the user has and subtracts the bet, letting they know how much they have

# giving the user differnt betting options, along with differnt outcomes on if they win or lose, and what their remaning balance is

    choice = input("Would you like to bet on a number, color, or odd/even?")
    if choice == "number":
        choice_number = input("What number would you like to bet on?")
        number = int(choice_number)
        roulette_number = random.randint(1,36)
        print("The number is", roulette_number)
        if number == roulette_number:
            print("You win!")
            print("You won $", roulette_bet*36)
            balance += roulette_bet * 36
            print("Your remaining balance is $", balance)
        else:
            print("You lose!")
            balance -= roulette_bet
            print("Your remaining balance is $", balance)

    if choice == "color":
        choice_color = input("What color would you like to bet on? (red or black)")
        color = choice_color
        roulette_color = random.choice(["red", "black"])
        print("The color is", roulette_color)
        if color == roulette_color:
            print("You win!")
            balance += roulette_bet * 2
            print("You won $", roulette_bet*2)
            print("Your remaining balance is $", balance)
        else:
            print("You lose!")
            balance -= roulette_bet
            print("Your remaining balance is $", balance)

    if choice == "odd/even":
        choice_odd_even = input("What would you like to bet on? (odd or even)")
        odd_even = choice_odd_even
        roulette_odd_even = random.randint(1,36)
        if roulette_odd_even % 2 == 0:
            result = "even"
        else:
            result = "odd"
        print("The number is", roulette_odd_even, "which is", result)
        if odd_even == result:
            print("You win!")
            print("You won $", roulette_bet*2)
            balance += roulette_bet * 2
            print("Your remaining balance is $", balance)
        else:
            print("You lose!")
            balance -= roulette_bet
            print("Your remaining balance is $", balance)

#allows the user to play as many rounds as they would like 
    choice = input("Play another hand? (yes/no): ")
    if choice == "no":
        playing = False
    if choice == "yes":
        continue
    else:
        print("Thank's for playing!")
    

        