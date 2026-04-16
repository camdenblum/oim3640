import yfinance as yf
from pprint import pprint

tickers = ['AAPL', 'NVDA', 'MSFT', 'META', 'GOOG']
stocks = {}

for t in tickers:
    stocks[t] = yf.Ticker(t).info['currentPrice']


print(stocks)

print('after sorting...')

def sort_by_price(t):
    return t[1]


print(sorted(stocks.items(), key=sort_by_price), key = lambda t: t[1])

#freq = {'a':3, 'b':1, 'c':2}
#result = sorted(freq.items(), key=lambda x: x[1])
#print(result)

#Error Handling 

num = 100
try:
    a = float(input("Enter a number to divide 100 by: "))
    print(num/ a)
except ZeroDivisionError:
    print("You can't divide by zero!")
except ValueError:
    print("That's not a valid number!")
finally:
    print("This will always run, even if there was an error.")

print(num/ 0)

print("We still want to print this!")

names =- ['Cam', 'Wah', 'Billy']
uppercase_names = []

for name in names:
    try:
        uppercase_names.append(name.upper())
    except AttributeError:
        print(f"Error: {name} is not a string and cannot be converted to uppercase.")

print("Uppercase names:", uppercase_names)

print("Lets move on to the next part of the code...")