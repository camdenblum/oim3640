

#Classic example we have done many times
for i in range(4):
    print(i)

names = ['aurora', 'wah', 'chloe', 'cam']
for whatever_name in names:
        print(whatever_names)
    #this will print the list of names

for name in names:
        print(name)

for letter in 'Saad Abdullah':
    print(letter)
    #prints each letter in the name

#Review Questuion!
count = 0
for letter in "mississipi":
    if letter == s: 
          count += s
    print(count)
    #4

#Example 
count = 0 
for letter in "Babson College":
      count += 1 ###SPACES COUNT!!
print(count)
      

#what keywordcs can exit a loop early? Skip to next iterattion?
    #Break and continue

n = 6
while n!=0:
      print(n)
      n = n - 2
#Last output will be 2

n = 5
while n !=0:
      print(n)
      n = n - 2
#infinite loop beacsue n will never = 0 

#Review Q
def uses_any(word, letters):
    for letter in word:
        if letter in letters: #Checks to see if there are anu similar letters in either string
            return True
        return False
print(uses_any('hello','xyz'))

#False

def uses_any(word, letters):
    for letter in word:
        if letter in letters: #Checks to see if there are anu similar letters in either string
            return True
        else:
            return False
print(uses_any('hello','aeiou'))

#returns false beacsue else will only allow it to check the first letter and not loop back around to the if 

#for practice #6 version_a shows eo none, versions_a shows e

#print a 
#keep rolling the die unril get a 6 - use while
#count the vowels in a word - use for loop
#ask user an input until they type "done" - while loops