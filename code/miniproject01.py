
print("Welcome to Cam's Crazy Casino!")
print("We offer games such as blackjack, roulette, and slots!")
choice_balance = input("How much would you like to deposit?")
balance = int(choice_balance)
choice = input("which game would you like to play?")

if choice == "blackjack":
    print("Great choice! Let's play some blackjack!")



#Blackjack Game

import random

playing = True

choice = input("would you like to play blackjack?")
choice_blackjack_bet = input("how much would you like to bet?") 
blackjack_bet = int(choice_blackjack_bet)
print("Your remaining balance is $", balance - blackjack_bet)

if choice == "yes":

    while playing:
        player_card = random.randint(1, 11)
        dealer_card = random.randint(1, 11)

        print("You drew:", player_card)
        print("Dealer drew:", dealer_card)

        choice = input("Would you like to hit or stand?: ")
        while choice == "hit":
            player_card = player_card + random.randint(1, 11)
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
                dealer_card = dealer_card + random.randint(1, 11)
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
        
        choice = input("Play another hand? (y/n): ")
        if choice == "n":
            playing = False
        if choice == "y":
            #how can we just loop back to the start of the game without having to copy and paste all of the code again?
            continue
        else:
            print("Goodbye!")

# Roulette Game

import random

playing = True

choice_roulette_bet = input("how much would you like to bet?") 
roulette_bet = int(choice_roulette_bet)
print("Your remaining balance is $", balance - roulette_bet)



