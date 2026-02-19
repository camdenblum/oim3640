import random

playing = True

choice = input("would you like to play blackjack?")

if choice == "yes":

    while playing:
        player_card = random.randint(1, 11)
        dealer_card = random.randint(1, 11)

        print("You drew:", player_card)
        print("Dealer drew:", dealer_card)

        choice = input("Would you like to hit or stand?: ")
        if choice == "hit":
            player_card = player_card + random.randint(1, 11)
            print(player_card)
            #while loop

        if choice == "stand":
            for dealer_card in range <= 17:
                dealer_card = dealer_card + random.randint(1, 11)

        if player_card > dealer_card:
            print("You win!")
        else:
            print("You lose")

        choice = input("Play another hand? (y/n): ")
        if choice == "n":
            playing = False
    else:
        print("Goodbye!")