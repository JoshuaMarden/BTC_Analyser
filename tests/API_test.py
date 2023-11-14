import ccxt

# Initialize the Binance exchange object
exchange = ccxt.binance()

# Fetch OHLCV data for BTC/USDT
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1d')  # '1d' for daily candles

for candle in ohlcv:
    timestamp, open, high, low, close, volume = candle
    print(f"{exchange.iso8601(timestamp)}: O={open} H={high} L={low} C={close} V={volume}")

