import yfinance as yf
import datetime

# Get the data for the last two days
today = datetime.date.today()
two_days_ago = today - datetime.timedelta(days=2)

SP500Info = yf.Ticker("^GSPC")
recent_data = SP500Info.history(start=two_days_ago, end=today, interval="1d")

# Select the last row to get the most recent data point
most_recent_data_point = recent_data.iloc[-1]

print(most_recent_data_point)