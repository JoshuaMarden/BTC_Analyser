import ccxt
import logging
import time
import datetime
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utilities import unix_to_ymd
from utilities import setup_logging

from config import DATA_DIR

# Setup logging
if len(sys.argv) > 1:
    logDir = sys.argv[1]
    print(f"log directory: {logDir}")
else:
    logDir = LOGS_DIR
    print(f"No specific log directory provided. Creating generic log"\
          "in logs folder.")

# Call the function from utilities.py to setup logging
setup_logging(logDir)
logging.info(f"--------------------------------------------")
logging.info(f"Downloading BTC data.")
logging.info(f"--------------------------------------------\n\n")
logging.info(f"\nThis script downloads in batches and only downloads new data\n"\
             "points added since last update.\n")


timeFrame = "1d"
currencyPair = "BTC/USDT"
exchangePlatform = "binance"
requestSize = 498 # max is 500ps

# Initialize the Binance exchange object
exchange = ccxt.binance()

# Initiate list with every data entry
try:
    btcDataFrame = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    lastRow = btcDataFrame.iloc[-1].tolist() # get last entry
    ohlcv = [lastRow]  # Making it a list of lists
    alreadyData = True
    # convert UTC date to a unix timestamp which is used by the server
    # and thus a necessary copnversion

    ymdDate = datetime.datetime.strptime(ohlcv[0][0], '%Y-%m-%d')
    unixTimestamp = int(ymdDate.timestamp())
    unixTimestamp = unixTimestamp * 1000
    ohlcv[0][0] = unixTimestamp

    logging.info("Historical data detected.")
    logging.info(f"Most recent timestamp in local database:   {unix_to_ymd(lastRow[0])}")
except FileNotFoundError:
    ohlcv = exchange.fetch_ohlcv(currencyPair, timeFrame, since=0, limit=1)
    logging.info("No historical data detected. Entire data set must be downloaded.")
    alreadyData = False

# Get the most recent data point from the online data base
# (when this date appears in our list, we know we have no more data to add)
mostRecentOnline = exchange.fetch_ohlcv(currencyPair, timeFrame, limit = 1)
logging.info(f"Most recent timestamp in online database:  {unix_to_ymd(mostRecentOnline[0][0])}")

batchNumber = 0
# Start sending off requests of candle data in batches
while (ohlcv[-1][0]) != (mostRecentOnline[0][0]):
    batchNumber = batchNumber + 1

    # Establish what time onwards we want data from
    getFrom = int(ohlcv[-1][0] + 1)
    print(f"sending off batch request for data #{batchNumber}")

    #send data request
    ohlcvBatch = exchange.fetch_ohlcv(currencyPair, timeFrame, since=getFrom, limit=requestSize)
    # for candle in ohlcvBatch:
        #print("List of batched candles:" + exchange.iso8601(candle[0]))
   
    # add that batch of data to the data list
    for candle in ohlcvBatch:
        # Add amended data to the list
        ohlcv.append(candle)

    # Update the most recent candle each loop
    # (just in case we get a new candle as the script is running)
    mostRecentOnline = exchange.fetch_ohlcv(currencyPair, timeFrame, limit = 1)

    time.sleep(1)


#Convert Unix time to YYYY-MM-DD
for dataPoint in ohlcv:
    dataPoint[0] = dataPoint[0] / 1000
    dataPoint[0] = datetime.datetime.utcfromtimestamp(dataPoint[0]).strftime('%Y-%m-%d')



# Store data
if batchNumber == 0:
   logging.info("Data up to date. Nothing to be appended.")
elif not alreadyData:
    logging.info(f"Sent off {batchNumber} requests.")
    # create brand spanking new df
    btcDataFrame = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    # Pickle the DataFrame
    btcDataFrame.to_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    logging.info(f"New data frame created from {str(len(ohlcv))} new data points and pickled.")
else:
    logging.info(f"Sent off {batchNumber} requests.")
    # convert the new data to a dataframe
    tempDataframe = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    # append the new data to the existing dataframe
    btcDataFrame = pd.concat([btcDataFrame, tempDataframe], axis=0, ignore_index=True)
    # drop any duplicate rows based on the timestamp (just in case)
    btcDataFrame.drop_duplicates(subset='Date', keep='last', inplace=True)
    # Save the updated dataframe
    btcDataFrame.to_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    logging.info(f"{str(len(ohlcv))} new data points downloaded.")
    logging.info("New data added to existing data frame.")

logging.info("BTC Dataframe:")
logging.info(btcDataFrame)
logging.info("\n\nScript Complete!\n\n")








