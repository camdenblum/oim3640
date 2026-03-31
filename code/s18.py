import yfinance as yf
from pprint import pprint

tickers = ['AAPL', 'NVDA', 'MSFT', 'META', 'GOOG']
stocks = {}

for t in tickers:
    stocks[t] = yf.Ticker(t).info['currentPrice']


print(stocks)
print(sorted(stocks.items()))

#freq = {'a':3, 'b':1, 'c':2}
#result = sorted(freq.items(), key=lambda x: x[1])
#print(result)

