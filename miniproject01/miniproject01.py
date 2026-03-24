file = open("../data/noahkahanbusyhead.txt")
file = open("../data/noahkahaniamiwas.txt")
file = open("../data/noahkahanstickseason.txt")

## Use pure python way to read the file and count the number of words in the file.
##refer to the instrutions in canvas


#  1: Open and read the files 
# .read() turns the whole file into one big string

busyhead = open("../data/noahkahanbusyhead.txt")
busyhead_lyrics = busyhead.read()
busyhead.close()

iamiwas = open("../data/noahkahaniamiwas.txt")
iamiwas_lyrics = iamiwas.read()
iamiwas.close()

stickseason = open("../data/noahkahanstickseason.txt")
stickseason_lyrics = stickseason.read()
stickseason.close()

# ── Step 2: Split the text into a list of words
# .split() breaks a string on spaces and newlines
# so "I was young" becomes ["I", "was", "young"]

busyhead_words    = busyhead_lyrics.split()
iamiwas_words     = iamiwas_lyrics.split()
stickseason_words = stickseason_lyrics.split()

# ── Step 3: Count word frequencies with a dictionary 
# We loop through every word; if we've seen it before we add 1,
# otherwise we start a new entry at 1.

def count_words(word_list):
    word_counts = {}
    for word in word_list:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    return word_counts

busyhead_counts    = count_words(busyhead_words)
iamiwas_counts     = count_words(iamiwas_words)
stickseason_counts = count_words(stickseason_words)

# ── Step 4: Get the top 10 words ─
# sorted() sorts the dictionary items by count (highest first)
# and returns a list of (word, count) tuples

def get_top_10(word_counts):
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:10]  # slice the first 10 items

# ── Step 5: Print the results 

print("=" * 40)


# We'll print stats for all three albums using a loop
# Each item in this list is a tuple: (album name, word list, word counts)
all_albums = [
    ("Busyhead",     busyhead_words,    busyhead_counts),
    ("I Am / I Was", iamiwas_words,     iamiwas_counts),
    ("Stick Season", stickseason_words, stickseason_counts),
]

for album_name, word_list, word_counts in all_albums:
    print("\nAlbum:", album_name)
    print("Total words:", len(word_list))       # len() counts list items
    print("Unique words:", len(word_counts))     # len() counts dictionary keys
    print("Top 10 words:")

    top_10 = get_top_10(word_counts)
    for word, count in top_10:
        print("  " + word + " - " + str(count) + " times")