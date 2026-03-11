
import random #lets the program shuffle the deck randomly
import time   # Allows the program to pause between messages
from rich.console import Console    # Used to print styled text to the terminal
from rich.table import Table    # Allows the program to display cards in a table format
from rich.panel import Panel    # Used to create boxed sections or messages in the interface

console = Console() # Creates a console object so we can use Rich formatting when printing


# This function prints text and pauses briefly to make the game feel more interactive
def slow_print(text, delay=0.35):
    console.print(text) # Prints the message to the screen
    time.sleep(delay)    # Waits a short time before continuing

# This function creates and shuffles a full 52 card deck
def create_deck():
    ranks = [str(n) for n in range(2, 11)] + ["J", "Q", "K", "A"]    # List of all possible card ranks in blackjack
    suits = ["♠", "♥", "♦", "♣"]     # List of the four card suits
    deck = [r + s for r in ranks for s in suits]     # Combines every rank with every suit to create a full deck of cards
    random.shuffle(deck)        # Randomly shuffles the deck so the order is unpredictable
    return deck

# This function extracts the rank from a card
# Example: "10♠" becomes "10" and "A♥" becomes "A"
def card_rank(card):
    return card[:-1]    # Removes the last character (the suit symbol)

# This function converts a card rank into its blackjack value
def card_value(rank):
    if rank in ("J", "Q", "K"):     # Face cards are worth 10
        return 10
    if rank == "A":     # Ace is initially worth 11
        return 11
    return int(rank)

# This function calculates the total value of a hand
def hand_value(cards):
    total = 0   # Keeps track of the total hand value
    aces = 0    # Counts how many Aces are in the hand
    for c in cards:     # Loop through every card in the player's hand
        r = card_rank(c)    # Get the card's rank
        v = card_value(r)    # Get the blackjack value of the rank
        total += v
        if r == "A":            # If the card is an Ace, increase the Ace counter
            aces += 1
     # If the hand is over 21 and there are Aces,
    # convert an Ace from 11 to 1 by subtracting 10
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

# This function prints the player's or dealer's hand to the screen
def show_hand(title, cards, hide_first=False):
    table = Table(show_header=False, box=None)      # Create a table without borders for clean formatting
    table.add_column()      # First column shows the hand label (Player or Dealer)
    table.add_column(justify="right")       # Second column shows the cards aligned to the right
    if hide_first:
        table.add_row(title, f"[bold]{cards[0]}[/bold] + [grey42]??[/grey42]")          # Show one card and hide the other with ??
    else:
        for i, c in enumerate(cards):   # Show every card in the hand
            r = card_rank(c)
            v = "1/11" if r == "A" else str(card_value(r))  # Get the card rank
            table.add_row(title if i == 0 else "", f"{c}  ({v})")   # Only print the title on the first row for cleaner formatting

    console.print(table)        # Print the table to the terminal

# This function formats money values nicely for the game display
def format_money(x):
    return f"${x:,.2f}"     # Converts a number into currency format (ex: 25 -> $25.00)


def get_float_input(prompt):
    while True:
        val = console.input(prompt)
        try:
            f = float(val)
            if f <= 0:
                console.print("Please enter a positive number.")
                continue
            return f
        except ValueError:
            console.print("Please enter a valid number.")


def get_bet(balance):
    while True:
        bet = get_float_input(f"Enter your bet (Balance: {format_money(balance)}): ")
        if bet > balance:
            console.print("You cannot bet more than your current balance.")
            continue
        return bet


def play_hand(balance):
    deck = create_deck()
    bet = get_bet(balance)
    old_balance = balance
    balance -= bet

    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    slow_print("Dealing cards...")
    show_hand("Player", player)
    console.print(f"Player total: {hand_value(player)}\n")
    show_hand("Dealer", dealer, hide_first=True)

    # Check initial blackjacks
    player_blackjack = hand_value(player) == 21 and len(player) == 2
    dealer_blackjack = hand_value(dealer) == 21 and len(dealer) == 2

    if player_blackjack or dealer_blackjack:
        console.print("\nDealer reveals hand:")
        show_hand("Dealer", dealer)
        if player_blackjack and dealer_blackjack:
            console.print(Panel("Push — both have blackjack. Your bet is returned.", title="Result"))
            balance += bet
        elif player_blackjack:
            payout = bet * 2.5  # bet was removed, so add back bet + 1.5x
            balance += payout
            console.print(Panel(f"Blackjack! You win {format_money(payout - bet)}.", title="Result"))
        else:
            console.print(Panel("Dealer has blackjack. You lose your bet.", title="Result"))

        net = balance - old_balance
        return balance, net

    # Player turn
    while True:
        choice = console.input("\nChoose action: [bold]hit[/bold] or [bold]stand[/bold]: ").strip().lower()
        if choice not in ("hit", "stand"):
            console.print("Type 'hit' or 'stand'.")
            continue
        if choice == "hit":
            player.append(deck.pop())
            show_hand("Player", player)
            player_total = hand_value(player)
            console.print(f"Player total: {player_total}")
            if player_total > 21:
                console.print(Panel("Bust! You exceeded 21 and lose your bet.", title="Result", style="red"))
                net = -bet
                return balance, net
            continue
        if choice == "stand":
            break

    # Dealer turn
    console.print("\nDealer reveals hand:")
    show_hand("Dealer", dealer)
    while hand_value(dealer) < 17:
        time.sleep(0.5)
        dealer.append(deck.pop())
        console.print("Dealer hits:")
        show_hand("Dealer", dealer)

    player_total = hand_value(player)
    dealer_total = hand_value(dealer)

    if dealer_total > 21:
        balance += bet * 2
        console.print(Panel(f"Dealer busts. You win {format_money(bet)}.", title="Result", style="green"))
        net = bet
    else:
        if player_total > dealer_total:
            balance += bet * 2
            console.print(Panel(f"You win! You gain {format_money(bet)}.", title="Result", style="green"))
            net = bet
        elif player_total == dealer_total:
            balance += bet
            console.print(Panel("Push — bet returned.", title="Result"))
            net = 0
        else:
            console.print(Panel("You lose your bet.", title="Result", style="red"))
            net = -bet

    return balance, net


def main():
    console.print(Panel("Welcome to Cam's Crazy Casino", style="bold cyan"))
    balance = get_float_input("How much would you like to deposit to start? ")

    while True:
        console.print(f"\nCurrent balance: [bold]{format_money(balance)}[/bold]")

        console.print("\nChoose a game to play:")
        console.print("- [bold]blackjack[/bold]: Classic 21 against the dealer")
        console.print("- [bold]roulette[/bold]: Bet on number, color, or odd/even")
        console.print("- [bold]quit[/bold]: Leave the casino")

        choice = console.input("\nEnter choice (blackjack/roulette/quit): ").strip().lower()
        if choice in ("quit", "q"):
            console.print(Panel(f"Leaving casino with {format_money(balance)} — thanks for playing!", style="bold green"))
            break

        if choice == "blackjack":
            balance, net = play_hand(balance)
            if net > 0:
                console.print(f"You won {format_money(net)}. New balance: {format_money(balance)}")
            elif net < 0:
                console.print(f"You lost {format_money(-net)}. New balance: {format_money(balance)}")
            else:
                console.print(f"No change. Balance: {format_money(balance)}")

        elif choice == "roulette":
            balance, net = play_roulette(balance)
            if net > 0:
                console.print(f"You won {format_money(net)}. New balance: {format_money(balance)}")
            elif net < 0:
                console.print(f"You lost {format_money(-net)}. New balance: {format_money(balance)}")
            else:
                console.print(f"No change. Balance: {format_money(balance)}")

        else:
            console.print("Please choose a valid option: 'blackjack', 'roulette', or 'quit'.")

        if balance <= 0:
            console.print(Panel("You have no more money — thanks for playing!", style="bold red"))
            break


def play_roulette(balance):
    console.print(Panel("Welcome to Roulette", style="bold magenta"))
    bet = get_bet(balance)
    old_balance = balance
    balance -= bet

    console.print(f"Bet placed: {format_money(bet)}. Remaining balance: {format_money(balance)}")

    console.print("Choose bet type: number, color, or odd/even")
    bet_type = console.input("Bet type: ").strip().lower()

    if bet_type == "number":
        num = None
        while num is None:
            val = console.input("Pick a number between 1 and 36: ")
            try:
                n = int(val)
                if 1 <= n <= 36:
                    num = n
                else:
                    console.print("Number must be between 1 and 36.")
            except ValueError:
                console.print("Enter a valid integer.")

        result_num = random.randint(1, 36)
        console.print(f"Wheel spins... The number is {result_num}")
        if num == result_num:
            payout = bet * 36
            balance += payout
            console.print(Panel(f"You hit the number! You win {format_money(payout - bet)}.", title="Result", style="green"))
            net = payout - bet
        else:
            console.print(Panel("No hit — you lose your bet.", title="Result", style="red"))
            net = -bet

    elif bet_type == "color":
        color = console.input("Pick a color (red or black): ").strip().lower()
        result_color = random.choice(["red", "black"])
        result_num = random.randint(1, 36)
        console.print(f"Wheel spins... The number is {result_num} which is {result_color}")
        if color == result_color:
            payout = bet * 2
            balance += payout
            console.print(Panel(f"Color hit! You win {format_money(payout - bet)}.", title="Result", style="green"))
            net = payout - bet
        else:
            console.print(Panel("Wrong color — you lose your bet.", title="Result", style="red"))
            net = -bet

    elif bet_type in ("odd", "even", "odd/even"):
        pick = console.input("Pick odd or even: ").strip().lower()
        result_num = random.randint(1, 36)
        result = "even" if result_num % 2 == 0 else "odd"
        console.print(f"Wheel spins... The number is {result_num} which is {result}")
        if pick == result:
            payout = bet * 2
            balance += payout
            console.print(Panel(f"You guessed correctly! You win {format_money(payout - bet)}.", title="Result", style="green"))
            net = payout - bet
        else:
            console.print(Panel("Wrong guess — you lose your bet.", title="Result", style="red"))
            net = -bet

    else:
        console.print("Invalid bet type. Bet returned.")
        balance += bet
        net = 0

    return balance, net


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nGoodbye — play again soon!")
