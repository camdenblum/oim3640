import yfinance as yf

#stocks = yf.Ticker("AAPL")
#info = stocks.info

#print(info.keys())
#print(len(info))
#print(info['longName'])
#print(info['shortName']) 
#print(info['currentPrice'])  
#print(info['longBusinessSummary'])

#print(info['longBusinessSummary'].split())
#print('iphone' in info['longBusinessSummary'].lower())

#print(info['city'])
#info['city'][0]= 'c'
#info['city'] = 'Wellesley'
#print(info['city'])

#info['founder'] = 'Robert'
#print(info['founder'])

#for k,v in info.items():
    #print(k, v)

tickers = ['AAPL', 'NVDA', 'MSFT']
prices = {}
for t in tickers:
    prices[t] = yf.Ticker(t).info['currentPrice']

print(sorted(prices)) #creating a new list of the keys in the dictionary, sorted alphabetically
print(sorted(prices.keys())) #same as above
print(sorted(prices.values()))
print(sorted(prices.values(), reverse = True)) #sorts the values in descending order
print(list(reversed(sorted(prices.values())))) #same as above but creates a new list instead of sorting in place

#how to sort stocks by values, but still to show k: v 


#print(tickers)
print(sum(prices.values()))

prices = {'AAPL': [252.52, 300], 'NVDA': [195.52, 250], 'MSFT': [300.52, 350], 'MSFT': [300.52, 350]}

total = 0 
for price in prices.values():
    total += price[1] ## to get the sum of the second value in the list for each stock, which is the current price.
print(total)

tickers.append('GOOG')
print(tickers)
for t in tickers:
    prices[t] = yf.Ticker(t).info['currentPrice']
print(prices)

stocks = {} #{'NVDA': [open, currentPrice, volume]}
for t in tickers:
    stocks[t] = yf.Ticker(t).info['open'], yf.Ticker(t).info['currentPrice'], yf.Ticker(t).info['volume']
print(stocks)

info_list = []
for name in ['open', 'currentPrice', 'volume']:
    info_list[name] = yf.Ticker(t).info[name]
stocks[t] = info_list

## Sets 

stocks = {'AAPL', 'NVDA', 'MSFT'}

unique_stocks = set(stocks)

unique_stocks 

unique_stocks.add('NVDA')

unique_stocks 

## difference in speed 

import timeit
words = open('data/words.txt').read().split()
word_set = set(words)     # 113K+ words

def search_list():
    return 'python' in words
def search_set():
    return 'python' in word_set

print('List:', timeit.timeit(search_list, number=1000))
print('Set: ', timeit.timeit(search_set, number=1000))
# List: 0.8500s  Set: 0.0003s

