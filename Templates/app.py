
from flask import Flask, render_template, request, jsonify, render_template_string
import yfinance as yf

app = Flask(__name__)

STOCK_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Stock Price Lookup</title>
    <style>
      body { font-family: Arial, sans-serif; padding: 1.5rem; }
      .card { max-width: 640px; margin: 1rem auto; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; }
      label { display:block; margin-bottom:0.5rem; }
      input { width:100%; padding:0.5rem; margin-bottom:0.75rem; box-sizing:border-box; }
      button { padding:0.5rem 0.9rem; }
      .result { background:#f0f9ff; border:1px solid #d8efff; padding:0.75rem; border-radius:6px; margin-top:0.5rem; }
      .error { color:#b00020; margin-top:0.5rem; }
      .meta { color:#666; font-size:0.9rem; }
    </style>
  </head>
  <body>
    <div class="card">
      <h1>Live Stock Price</h1>
      <form method="post" action="/stock">
        <label for="symbol">Ticker symbol</label>
        <input id="symbol" name="symbol" type="text" placeholder="e.g. AAPL" value="{{ symbol or '' }}" autofocus>
        <button type="submit">Get Price</button>
      </form>

      {% if error %}
        <div class="error">{{ error }}</div>
      {% endif %}

      {% if price is not none %}
        <div class="result">
          <div><strong>{{ name or symbol }}</strong> — <span style="font-size:1.25rem;">${{ '%.2f'|format(price) }}</span></div>
          <div class="meta">As reported by yfinance / Yahoo Finance</div>
        </div>
      {% elif symbol and price is none and not error %}
        <div class="meta">No price available.</div>
      {% endif %}
    </div>
  </body>
</html>
"""


def lookup_price(symbol: str):
    """Return (price: float|None, name: str|None, error: str|None)."""
    symbol = (symbol or '').strip().upper()
    if not symbol:
        return None, None, 'No symbol provided.'

    try:
        ticker = yf.Ticker(symbol)
        # try history close first
        hist = ticker.history(period='1d')
        price = None
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
        else:
            # fallback to fast_info or info
            fast = getattr(ticker, 'fast_info', None)
            if fast and isinstance(fast, dict) and fast.get('last_price') is not None:
                price = float(fast['last_price'])
            else:
                info = getattr(ticker, 'info', None) or {}
                price = info.get('regularMarketPrice')

        info = getattr(ticker, 'info', None) or {}
        name = info.get('shortName') or info.get('longName') or symbol
        if price is None:
            return None, name, f'No price available for {symbol}.'
        return float(price), name, None
    except Exception:
        return None, None, f'Error fetching data for {symbol}.'


@app.route('/')
def index():
    return render_template_string(STOCK_PAGE, symbol=None, price=None, name=None, error=None)


@app.route('/stock', methods=['GET', 'POST'])
def stock_page():
    # Accept ?symbol= via GET or form POST
    symbol = None
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').strip().upper()
    else:
        symbol = request.args.get('symbol', '')
        if symbol:
            symbol = symbol.strip().upper()

    price = None
    name = None
    error = None
    if symbol:
        price, name, error = lookup_price(symbol)

    return render_template_string(STOCK_PAGE, symbol=symbol, price=price, name=name, error=error)


@app.route('/api/stock')
def stock_api():
    # JSON API: /api/stock?symbol=AAPL
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'symbol query parameter required'}), 400
    price, name, error = lookup_price(symbol)
    if error:
        return jsonify({'symbol': symbol, 'error': error}), 404
    return jsonify({'symbol': symbol, 'name': name, 'price': price})

@app.get("/ticker")
def ticker ():
    return render_template("stock-form.html")


if __name__ == '__main__':
    app.run(debug=True)
