import yfinance as yahFin
import datetime
import time
import sys
import os
import pandas as pd
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from utilities import setup_logging

dataName = "SP500"
ticker = "^GSPC" # ticker required

# Setup logging
if len(sys.argv) > 1:
    logDir = sys.argv[1]
    print(f"log directory: {logDir}")
else:
    raise ValueError("The dated log directory was not provided as an argument.")

# Call the function from utilities.py to setup logging
setup_logging(logDir)

logging.info(f"\n\nDownloading S&P 500 data.\n")
logging.info(f"\nThis script downloads in batches and only downloads new data\n\
             points added since last update that are also in the BTC data.\n")


# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    
    dataFrom = datetime.datetime.strptime(BTCdataframe.iloc[0, 0], "%Y-%m-%d") # First date that we have BTC data for
    dataUntil = datetime.datetime.strptime(BTCdataframe.iloc[-1, 0], "%Y-%m-%d") # Most recent datre that we have BTC data for
    
    dataUntil = dataUntil.date()
    dataFrom = dataFrom.date()

    logging.info("Historical BTC data detected.")
    logging.info(f"Date of first BTC record :   {dataFrom}")
    logging.info(f"Most recent BTC timestamp:   {dataUntil}")


except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()

try:
    existingDataFrame = pd.read_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    dataFrom = existingDataFrame.iloc[-1, 0] # Get last entry of SP500 data
    logging.info(f"Historical {dataName} data detected, most recent entry:\
                  {dataFrom}.")
    alreadyData = True #note that we already have data stored

except FileNotFoundError:
    alreadyData = False #note that we already have data stored
    logging.info(f"No historical data detected - downlading from {dataFrom}.")

if dataFrom == dataUntil: # if the data matched we can just terminate the script now
    logging.info(f"Data for {dataName} dates matches data for BTC dates.")
    logging.info(f"Terminating script.")
    sys.exit()

# Get data starting date 7 days before our BTC data start date in case

# Now we want the data for out ticker over the same period as we have 
# our BTC data.
# dates are not in the datatframe online so we need to get a list of the 
# dates we want and then send off for them in batches.

tickerInfo = yahFin.Ticker(ticker) # ticker required
ohlcvDF = pd.DataFrame()

logging.info(f"Gathering data for {dataName}...")
logging.info(f"Gathering data for range {dataFrom} : {dataUntil}")

# we have to forward fill data
sevenDaysPrior = dataFrom - datetime.timedelta(days=7) # So we can forward fill data
# setup the time change/delta for each iteration
delta = datetime.timedelta(days=1)
workingDate = sevenDaysPrior
dates = []

# iterate through dates adding one each time
# creates a list of dates that we are to fetch data for
while workingDate <= dataUntil:
    dates.append(workingDate)
    workingDate += delta


# Setup vars for batch requesting
batchSize = 498
finalBatch = False
batchIndexStart = 0
batchIndexEnd = 0 + batchSize
batch = 0

# send of batch requests
while not finalBatch:
    
     # handles getting to end of the number of dates to fetch
    if batchIndexEnd > len(dates): 
        # If the size of the next batch exceeds number of remaining dates
        # we need to request data for....
        batchIndexEnd = len(dates) -1 # Size the batch to match the no. remaining dates
        finalBatch = True # While loop terminating boolean
        # send off final batch
        ohlcvBatchDF = tickerInfo.history(start = dates[batchIndexStart],\
                                end = dataUntil, interval="1d")

    # handles all other iterations, simply sends off batch requests
    else: 
        ohlcvBatchDF = tickerInfo.history(start = dates[batchIndexStart],\
                                        end = dates[batchIndexEnd], interval="1d")
        time.sleep(1)
    
    # Keep track of no. batches sent for record purposes
    batch = batch + 1
    
    logging.info("Normalising dates")
    #Convert date time in index to just time
    ohlcvBatchDF.index = ohlcvBatchDF.index.date
    # Move date out of index to a new column because it's awkward
    ohlcvBatchDF = ohlcvBatchDF.reset_index()
    ohlcvBatchDF.rename(columns={'index': 'Date'}, inplace=True)

    
    # concat newest batch with previous batch dataframes
    ohlcvDF = pd.concat([ohlcvDF, ohlcvBatchDF], axis=0, ignore_index=False)
    
    logging.info(f"Batch #{batch} received and stored for period: "\
                 f"{dates[batchIndexStart]} : {dates[batchIndexEnd]}")
    
    # Updates batch indicies for next batch request
    batchIndexStart = batchIndexStart + batchSize
    batchIndexEnd = batchIndexEnd + batchSize


if not batch == 0:
    # This next step of data handling is obviously only necessary
    # if we actually obtained data that we need to work with.

    logging.info("Forward filling missing data")

    # Add the missing dates to the dataframe
    datesSet = set(ohlcvDF["Date"])
    missingDates = []
    for date in dates:
        if not date in datesSet:
            missingDates.append(date)

    for missingDate in missingDates:
        ohlcvDF.loc[len(ohlcvDF)] = {'Date': missingDate}

    ohlcvDF = ohlcvDF.sort_values(by='Date')
    ohlcvDF = ohlcvDF.ffill().reset_index(drop=True)
    
 
    # Now we remove the dates from before the first date 
    # of our btc data
    btcdataFromIndex = ohlcvDF.loc[ohlcvDF['Date']\
                                        == dataFrom].index[0]
    ohlcvDF = ohlcvDF.iloc[btcdataFromIndex:]
    ohlcvDF = ohlcvDF.reset_index(drop=True)

# Store data
if batch == 0:
   logging.info(f"{dataName} Data up to date. Nothing to be appended.")
elif not alreadyData:
    logging.info(f"Sent off {batch} requests.")
    # create brand spanking new df
    ohlcvDF.to_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    logging.info(f"New data frame created from {str(len(ohlcvDF))} new data points and pickled.")
else:
    logging.info(f"Sent off {batch} requests.")
    btcDataFrame = pd.concat([existingDataFrame, ohlcvDF], axis=0, ignore_index=True)
    # drop any duplicate rows based on the timestamp (just in case)
    btcDataFrame.drop_duplicates(subset='Date', keep='last', inplace=True)
    # Save the updated dataframe
    ohlcvDF.to_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    logging.info(f"{str(len(ohlcvDF))} new data points downloaded.")
    logging.info("New data added to existing data frame.")


print(ohlcvDF)