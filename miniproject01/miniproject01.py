
import matplotlib.pyplot as plt  # bar charts
import pandas as pd              # the "easier way" — for comparison

# ── Load the files ───────────────────────────────────────────

file1 = open("../data/noahkahanbusyhead.txt")
busyhead_lyrics = file1.read()
file1.close()

file2 = open("../data/noahkahaniamiwas.txt")
iamiwas_lyrics = file2.read()
file2.close()

file3 = open("../data/noahkahanstickseason.txt")
stickseason_lyrics = file3.read()
file3.close()

albums = {
    "Busyhead":     busyhead_lyrics,
    "I Am / I Was": iamiwas_lyrics,
    "Stick Season": stickseason_lyrics
}

# ── Text cleaning ────────────────────────────────────────────

STOP_WORDS = ["the", "and", "i", "a", "to", "of", "in", "you",
              "my", "it", "is", "me", "that", "we", "on", "be",
              "with", "your", "for", "was", "but", "so", "no",
              "not", "just", "oh", "all", "up", "out", "do",
              "an", "or", "if", "at", "he", "she", "they", "its",
              "ll", "ve", "re", "s", "t", "m"]  # leftover fragments

def clean_text(text):
    text = text.lower()
    for char in [",", ".", "!", "?", "'", '"', "(", ")", "-", "\n", ":"]:
        text = text.replace(char, " ")
    return text

def count_words(text, remove_stop_words=True):
    cleaned = clean_text(text)
    word_list = cleaned.split()
    word_counts = {}
    for word in word_list:
        if remove_stop_words and word in STOP_WORDS:
            continue
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    return word_counts

def get_top_words(word_counts, n=10):
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_words[:n]

# ── Feature 1: Full album report ────────────────────────────
# Prints a formatted summary for all three albums

def print_album_report():
    print("\n" + "=" * 50)
    print("   NOAH KAHAN LYRICS — FULL ALBUM REPORT")
    print("=" * 50)

    for album_name in albums:
        raw_words  = clean_text(albums[album_name]).split()
        counts     = count_words(albums[album_name])
        top        = get_top_words(counts, n=5)

        print("\n  Album : " + album_name)
        print("  Total words  : " + str(len(raw_words)))
        print("  Unique words : " + str(len(counts)))
        print("  Top 5 words  :")
        for word, num in top:
            # Build a simple text bar out of "█" characters
            bar = "█" * num
            print("    " + word.ljust(15) + str(num).rjust(4) + "  " + bar[:30])

    print("\n" + "=" * 50)

# ── Feature 2: Word search ───────────────────────────────────

def search_word(word):
    word = word.lower().strip()
    print("\n  Searching for: '" + word + "'")
    print("  " + "-" * 30)
    for album_name in albums:
        counts = count_words(albums[album_name])
        result = counts.get(word, 0)
        print("  " + album_name.ljust(16) + str(result) + " time(s)")

# ── Feature 3: Phrase search ─────────────────────────────────

def search_phrase(phrase):
    phrase = phrase.lower().strip()
    print("\n  Searching for phrase: '" + phrase + "'")
    print("  " + "-" * 30)
    for album_name in albums:
        cleaned = clean_text(albums[album_name])
        count   = cleaned.count(phrase)
        print("  " + album_name.ljust(16) + str(count) + " time(s)")

# ── Feature 4: Bar chart for one album ──────────────────────

def make_bar_chart(album_name):
    counts    = count_words(albums[album_name])
    top_words = get_top_words(counts, n=8)

    words  = [pair[0] for pair in top_words]
    totals = [pair[1] for pair in top_words]

    plt.figure(figsize=(9, 5))
    plt.bar(words, totals, color="steelblue", edgecolor="white")
    plt.title("Top Words — " + album_name, fontsize=14)
    plt.xlabel("Word")
    plt.ylabel("Frequency")
    plt.tight_layout()

    filename = "../output/" + album_name.replace(" ", "_") + "_chart.png"
    plt.savefig(filename)
    plt.show()
    print("  Chart saved to: " + filename)

# ── Feature 5: Save results to a text file ──────────────────
# This writes a summary so you can share your findings

def save_results():
    output = open("../output/results_summary.txt", "w")
    output.write("Noah Kahan Lyrics Analysis\n")
    output.write("=" * 40 + "\n\n")

    for album_name in albums:
        raw_words = clean_text(albums[album_name]).split()
        counts    = count_words(albums[album_name])
        top       = get_top_words(counts, n=10)

        output.write("Album: " + album_name + "\n")
        output.write("Total words: "  + str(len(raw_words)) + "\n")
        output.write("Unique words: " + str(len(counts))    + "\n")
        output.write("Top 10 words:\n")
        for word, num in top:
            output.write("  " + word + ": " + str(num) + "\n")
        output.write("\n")

    output.close()
    print("\n  Results saved to ../output/results_summary.txt")

# ── Feature 6: Pandas comparison ────────────────────────────
# This does the same word-count job using pandas.
# After building everything by hand, this shows how a library
# can do the same thing in fewer lines.

def pandas_comparison(album_name):
    print("\n  [Pandas version — same result, different approach]")

    cleaned   = clean_text(albums[album_name])
    word_list = cleaned.split()

    # pandas Series works like a list but has built-in counting tools
    series = pd.Series(word_list)

    # Remove stop words using a pandas filter
    filtered = series[~series.isin(STOP_WORDS)]

    # .value_counts() does what our dictionary loop did — in one line!
    top = filtered.value_counts().head(10)

    print("  Top 10 words in " + album_name + " (via pandas):")
    print(top.to_string())

# ── Interactive menu ─────────────────────────────────────────

print("Welcome to the Noah Kahan Lyrics Explorer!")

while True:
    print("\nWhat would you like to do?")
    print("1 - Full album report")
    print("2 - Search for a word")
    print("3 - Search for a phrase")
    print("4 - Show bar chart for an album")
    print("5 - Save results to a file")
    print("6 - Pandas comparison (library vs. built-in)")
    print("7 - Quit")

    choice = input("Enter your choice: ").strip()

    if choice == "1":
        print_album_report()

    elif choice == "2":
        word = input("Enter a word: ")
        search_word(word)

    elif choice == "3":
        phrase = input("Enter a phrase: ")
        search_phrase(phrase)

    elif choice == "4":
        print("Albums: Busyhead / I Am / I Was / Stick Season")
        name = input("Enter album name: ").strip()
        if name in albums:
            make_bar_chart(name)
        else:
            print("Album not found — check your spelling!")

    elif choice == "5":
        save_results()

    elif choice == "6":
        print("Albums: Busyhead / I Am / I Was / Stick Season")
        name = input("Enter album name: ").strip()
        if name in albums:
            pandas_comparison(name)
        else:
            print("Album not found — check your spelling!")

    elif choice == "7":
        print("Goodbye!")
        break

    else:
        print("Please enter a number between 1 and 7.")




