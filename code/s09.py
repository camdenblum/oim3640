
#i = 0 
#while i < 5:
 #       print(i)
  #      i += 1

#responses = ""
#while responses != "quit":
     #responses = input("Enter Command: ")
      #  print(f"You said: {responses}")


#words = ["hello, "world", "target", "python"]
#for w in words:
 #       print('checkking:', w)
  #      if w == "target":
   #         print("Found it!\n")
    #        continue
     #   print(num) #prints odd numbers only

#continue - skip to the next itteration
#for num in range(10):
 #   if num % 2 ==0: 
  #      continue
   # print(num) # prints odd numbers only

#print(f(10)) # prints all of the odd numbers (1, 3, 5, 7, 9)
    # of print is chnaged to return it will only produce (1)
# AI Code that I may use for mini project 

import random

while playing:
    player_card = random.randint(1, 11)
    dealer_card = random.randint(1, 11)

    print("You drew:", player_card)
    print("Dealer drew:", dealer_card)

    choice = input("Would you like to hit or stand?: ")
    if choice == "hit":
         player_card = player_card + random.randint(1, 11)
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
