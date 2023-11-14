import ccxt
import logging
import time
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from config import LOGS_DIR
from utilities import unix_to_ymd
from utilities import unix_to_ymdhms


# Setup logging
timeExecuted = time.strftime("%Y%m%d_%H%M%S")
logName = os.path.join(LOGS_DIR, f'BTC_download_log_{timeExecuted}.txt')
# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(logName),
                              logging.StreamHandler()])

timeFrame = "1d"
currencyPair = "BTC/USDT"
exchangePlatform = "binance"
requestSize = 498 # max is 500ps

# Initialize the Binance exchange object
exchange = ccxt.binance()

# Initiate list with every data entry
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    lastRow = BTCdataframe.iloc[-1].tolist() # get last entry
    ohlcv = [lastRow]  # Making it a list of lists
    alreadyData = True

    logging.info("Historical data detected.")
    logging.info(f"Most recent timestamp in local database:   {unix_to_ymdhms(int(lastRow[0]))}")
except FileNotFoundError:
    ohlcv = exchange.fetch_ohlcv(currencyPair, timeFrame, since=0, limit=1)
    logging.info("No historical data detected. Entire data set must be downloaded.")
    alreadyData = False

# Get the most recent data point from the online data base
# (when this date appears in our list, we know we have no more data to add)
mostRecentOnline = exchange.fetch_ohlcv(currencyPair, timeFrame, limit = 1)
logging.info(f"Most recent timestamp in online database:  {unix_to_ymdhms(int(mostRecentOnline[0][0]))}")

batchNumber = 0
# Start sending off requests of candle data in batches
while int(ohlcv[-1][0]) != mostRecentOnline[0][0]:
    batchNumber = batchNumber + 1

    # Establish what time onwards we want data from
    getFrom = int(ohlcv[-1][0] + 1)
    print(f"sending off batch request for data [{batchNumber}]")

    #send data request
    ohlcvBatch = exchange.fetch_ohlcv(currencyPair, timeFrame, since=getFrom, limit=requestSize)
    # for candle in ohlcvBatch:
        #print("List of batched candles:" + exchange.iso8601(candle[0]))
   
    # add that batch of data to the data list
    for candle in ohlcvBatch:
        # Add amended data to the list
        ohlcv.append(candle)

    # Update the most recent candle
    # (just in case we get a new candle as the script is running)
    mostRecentOnline = exchange.fetch_ohlcv(currencyPair, timeFrame, limit = 1)

    time.sleep(1)


# Store data
if batchNumber == 0:
   logging.info("Data up to date. Nothing to be appended.")
elif not alreadyData:
    logging.info(f"Sent off {batchNumber} requests.")
    # create brand spanking new df
    BTCdataframe = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # Pickle the DataFrame
    BTCdataframe.to_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    logging.info(f"New data frame created from {str(len(ohlcv))} new data points and pickled.")
else:
    logging.info(f"Sent off {batchNumber} requests.")
    # convert the new data to a dataframe
    tempDataframe = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # append the new data to the existing dataframe
    BTCdataframe = pd.concat([BTCdataframe, tempDataframe], axis=0, ignore_index=True)
    # drop any duplicate rows based on the timestamp (just in case)
    BTCdataframe.drop_duplicates(subset='timestamp', keep='last', inplace=True)
    # Save the updated dataframe
    BTCdataframe.to_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    logging.info(f"{str(len(ohlcv))} new data points downloaded.")
    logging.info("New data added to existing data frame.")

print(BTCdataframe)








