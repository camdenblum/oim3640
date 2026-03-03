Mini Project #0

## My Project Proposal

**What I'm building:** 
I am building a Python terminal-based casino app where a single user can play Blackjack and Roulette. The user will deposit a starting balance at the beginning of the session, place bets each round, and the program will update their balance and track session performance.

**Why I chose this:** 
I chose this project because it’s a good fit for a beginner learning Python while still being challenging. It uses core programming skills (loops, conditionals, functions, lists/dictionaries, randomness, and input validation). Since I already understand the rules of these games, I can focus on accurately translating real game logic into working code.

**Core features:** 
 The application will begin with a main menu that allows the user to choose between Blackjack and Roulette or quit the program. The user will deposit an initial balance at the start of the session and place bets before each round. The system will prevent users from betting more than their available balance and will update their balance after each win or loss. The Blackjack game will use a full 52-card deck, include face cards valued at ten, and implement Ace logic that allows it to count as either one or eleven depending on the hand. Cards will be removed from the deck as they are dealt to ensure accuracy, and the dealer will follow standard rules such as hitting until reaching at least seventeen. The Roulette game will simulate a realistic spin result and allow users to place number bets, color bets, or odd/even bets with correct payout logic for each type.

**What I don't know yet:** 
While I understand the overall structure of the games, I still need to learn how to organize the program into clean, modular functions so that each game runs independently from the main menu. I also need to implement a properly managed deck system for Blackjack where cards are removed after being dealt and reshuffled when necessary. Additionally, I will need to strengthen my input validation skills to ensure the program handles incorrect or unexpected user input without crashing. Improving these structural and technical elements will be a key learning objective of this project.

## Feedback

Have to find another random function to account for multiple 10's in a blackjack deck.
Use import sys. to make the print function look smoother


