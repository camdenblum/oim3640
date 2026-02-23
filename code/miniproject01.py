
## This is the start of the app where we welcome the user and give them an option to deposit money and choose a game to play. 

print("Welcome to Cam's Crazy Casino!")
print("We offer games such as blackjack, roulette, and craps!")
choice_balance = input("How much would you like to deposit?")
balance = int(choice_balance)
choice = input("which game would you like to play?")

if choice == "blackjack":
    print("Great choice! Let's play some blackjack!")
## Add a section that displays overall win percentage in each game and how much credit won/lost


#Blackjack Game

import random

playing = True

#allows user to place a bet
choice_blackjack_bet = input("how much would you like to bet?") 
blackjack_bet = int(choice_blackjack_bet)
print("Your remaining balance is $", balance - blackjack_bet)


if choice == "blackjack":

#while loops allows the user to play as many hands as they like until they want to stop. Randit allows for random card selection.
    while playing:
        player_card = random.randint(1,11)
        dealer_card = random.randint(1,11)

        print("You drew:", player_card)
        print("Dealer drew:", dealer_card)
        player_card = player_card + random.randint(1,11)
        print("You drew:", player_card)
        #Note: we do not print dealers second card as in the rules the player does not see it
        dealer_card = random.randint(1, 11) + dealer_card
      
#allows the user to make a decision on how they want to play, along with the functions that determine if they win or lose
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
                balance += blackjack_bet * 2
                print("Your remaining balance is $", balance)
                break
            choice = input("Would you like to hit or stand?: ")

        if choice == "stand":
            print("Dealer has:", dealer_card)
            while dealer_card < 17:
                dealer_card = dealer_card + random.randint(1,11)
                print("Dealer drew:", dealer_card)

        if player_card > dealer_card and player_card <= 21:
            print("You win!")
            print("You won $", blackjack_bet*2)
            balance += blackjack_bet * 2
            print("Your remaining balance is $", balance)

        elif dealer_card > 21:
            print("You win!")
            print("You won $", blackjack_bet*2)
            balance += blackjack_bet * 2
            print("Your remaining balance is $", balance)
        elif player_card < dealer_card:
            print("You lose")
            print("Your remaining balance is $", balance - blackjack_bet)
#allows the user to play as many hands as they like until they want to stop.
        choice = input("Play another hand? (yes/no): ")
        if choice == "no":
            playing = False
        if choice == "yes":
            continue
        else:
            print("Thank's for playing!")

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
            print("Your remaining balance is $", balance - roulette_bet)

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
            balance += roulette_bet * 2
            print("Your remaining balance is $", balance)
        else:
            print("You lose!")
            print("Your remaining balance is $", balance - roulette_bet)
#allows the user to play as many rounds as they would like 
    choice = input("Play another hand? (yes/no): ")
    if choice == "no":
        playing = False
    if choice == "yes":
        continue
    else:
        print("Thank's for playing!")
    

        