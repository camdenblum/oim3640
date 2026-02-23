
print("Welcome to Cam's Crazy Casino!")
print("We offer games such as blackjack, roulette, and slots!")
choice_balance = input("How much would you like to deposit?")
balance = int(choice_balance)
choice = input("which game would you like to play?")

if choice == "blackjack":
    print("Great choice! Let's play some blackjack!")
## Add a section that displays overall win percentage in each game and how much credit won/lost


#Blackjack Game

import random

playing = True

choice_blackjack_bet = input("how much would you like to bet?") 
blackjack_bet = int(choice_blackjack_bet)
print("Your remaining balance is $", balance - blackjack_bet)

if choice == "blackjack":

    while playing:
        player_card = random.randint(1,11)
        dealer_card = random.randint(1,11)

        print("You drew:", player_card)
        print("Dealer drew:", dealer_card)
        player_card = player_card + random.randint(1,11)
        print("You drew:", player_card)
        dealer_card = random.randint(1, 11) + dealer_card
      

        choice = input("Would you like to hit or stand?: ")
        while choice == "hit":
            player_card = player_card + random.randint(1,11)
            print("You drew:", player_card)
            if player_card > 21:
                print("you bust!")
                print("Your remaining balance is $", balance - blackjack_bet)
            if player_card == 21:
                print("Blackjack!")
                print("You won $", blackjack_bet*2)
                print("Your remaining balance is $", balance + blackjack_bet*2)
                break
            choice = input("Would you like to hit or stand?: ")

        if choice == "stand":
            while dealer_card < 17:
                dealer_card = dealer_card + random.randint(1,11)
                print("Dealer drew:", dealer_card)

        if player_card > dealer_card and player_card <= 21:
            print("You win!")
            print("You won $", blackjack_bet*2)
            print("Your remaining balance is $", balance + blackjack_bet*2)

        elif dealer_card > 21:
            print("You win!")
            print("You won $", blackjack_bet*2)
            print("Your remaining balance is $", balance + blackjack_bet*2)
        elif player_card < dealer_card:
            print("You lose")
            print("Your remaining balance is $", balance - blackjack_bet)
        
        choice = input("Play another hand? (yes/no): ")
        if choice == "no":
            playing = False
        if choice == "yes":
            #how can we just loop back to the start of the game without having to copy and paste all of the code again?
            continue
        else:
            print("Goodbye!")

# Roulette Game

import random

playing = True

if choice == "roulette":
    print("Great choice! Let's play some roulette!")

while playing:

    choice_roulette_bet = input("how much would you like to bet?") 
    roulette_bet = int(choice_roulette_bet)
    print("Your remaining balance is $", balance - roulette_bet)

    choice = input("Would you like to bet on a number, color, or odd/even?")
    if choice == "number":
        choice_number = input("What number would you like to bet on?")
        number = int(choice_number)
        roulette_number = random.randint(1,36)
        print("The number is", roulette_number)
        if number == roulette_number:
            print("You win!")
            print("You won $", roulette_bet*36)
            print("Your remaining balance is $", balance + roulette_bet*36)
        else:
            print("You lose!")
            print("Your remaining balance is $", balance - roulette_bet)

    if choice == "color":
        choice_color = input("What color would you like to bet on? (red or black)")
        color = choice_color
        roulette_color = random.choice(["red", "black"])
        print("The color is", roulette_color)
        if color == roulette_color:
            print("You win!")
            print("You won $", roulette_bet*2)
            print("Your remaining balance is $", balance + roulette_bet*2)
        else:
            print("You lose!")
            print("Your remaining balance is $", balance - roulette_bet)

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
            print("Your remaining balance is $", balance + roulette_bet*2)
        else:
            print("You lose!")
            print("Your remaining balance is $", balance - roulette_bet)
    choice = input("Play another hand? (yes/no): ")
    if choice == "no":
        playing = False
    if choice == "yes":
        continue
    else:
        print("Goodbye!")
        