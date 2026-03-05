def uses_only(word, letters):
    for letter in word:
        if letter not in letters:
            return False
    return True

def must_use(word, required):
    for letter in required:
        if letter not in word:
            return False
    return True

def find_words(letters, required):
    with open('data/words.txt') as f:
        words = f.read().splitlines()
    valid_words = []
    for word in words:
        if uses_only(word, letters) and must_use(word, required):
            valid_words.append(word)
    return valid_words

def uses_all(word, letters):
    for letter in letters:
        if letter not in word:
            return False
    return True

def is_abecedarian(word):
    for i in range(len(word) - 1):
        if word[i] > word[i + 1]:
            return False
    return True

def main():
    Letters = input("enter the letters you want to use: ")
    Required = input("enter the letters that are required to be in the word: ")
    valid_words = find_words(Letters, Required)
    print("Valid words:", valid_words)

if __name__ == "__main__":
    main()
