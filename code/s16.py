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