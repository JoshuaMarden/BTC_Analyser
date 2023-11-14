import requests

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=22GE7P5BJCTE5QIG'
r = requests.get(url)
data = r.json()

print(data)