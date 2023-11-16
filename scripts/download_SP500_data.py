import yfinance as yahFin
import datetime
import time
import sys
import os
import pandas as pd
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import LOGS_DIR, DATA_DIR
from utilities import setup_logging

dataName = "SP500" # used to name data
ticker = "^GSPC" # ticker required for download

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
logging.info(f"Downloading S&P 500 data.")
logging.info(f"--------------------------------------------")
logging.info(f"\nThis script downloads in batches and only downloads new data\n\
               points added since last update that are also in the BTC data.\n")


# Check for BTC data
try:
    # check for BTC data already stored locally 
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    
    dataFrom = datetime.datetime.strptime(BTCdataframe.iloc[0, 0], "%Y-%m-%d") # First date that we have BTC data for
    dataUntil = datetime.datetime.strptime(BTCdataframe.iloc[-1, 0], "%Y-%m-%d") # Most recent datre that we have BTC data for
    # Remove time from the date time variable as we only need the date
    dataUntil = dataUntil.date()
    dataFrom = dataFrom.date()

    logging.info("Historical BTC data detected.")
    logging.info(f"Date of first BTC record :   {dataFrom}")
    logging.info(f"Most recent BTC timestamp:   {dataUntil}")


except FileNotFoundError:
    # If we don't have BTC data, we can't know what dates to fetch
    #  yfinance data for
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()

try: #check for existsing local data for ticker
    existingDataFrame = pd.read_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    dataFrom = existingDataFrame.iloc[-1, 0] # Get last entry of SP500 data
    logging.info(f"Historical {dataName} data detected, most recent entry:\
                  {dataFrom}.")
    alreadyData = True # note that we already have data stored

except FileNotFoundError:
    alreadyData = False # note that we do not already have data stored
    logging.info(f"No historical data detected - downlading from {dataFrom}.")

if dataFrom == dataUntil: # if the data matches BTC data we can just terminate the script now
    logging.info(f"Data for {dataName} dates matches data for BTC dates.")
    logging.info(f"Terminating script - no action needed.")
    logging.info("\n\nScript Complete!\n\n")
    sys.exit()


# Get data starting date 7 days BEFORE our BTC data start date in case
# we have to forward fill missing ticker data

# Now we want the data for our ticker over the same period as we have 
# our BTC data.

# dates are not in the provided when we download the ticker data,
# we have to outline what the start and end dates we want
# dates we want and then send off for them in batches.

tickerInfo = yahFin.Ticker(ticker) # ticker required
ohlcvDF = pd.DataFrame() # initiate dataframe to store data

logging.info(f"Gathering data for {dataName}...")
logging.info(f"Gathering data for range {dataFrom} : {dataUntil}")

# get data from before first date of BTC data for forward filling
sevenDaysPrior = dataFrom - datetime.timedelta(days=7)
# setup the time change/delta for each iteration
delta = datetime.timedelta(days=1)
# workingDate is our extended start date
workingDate = sevenDaysPrior
# initialise list to store the dates in
dates = []

# iterate through dates adding one each time, this
# creates a list of the dates we are getting data from for our ticker
while workingDate <= dataUntil:
    dates.append(workingDate)
    workingDate += delta


# Declare variables for batch requesting
batchSize = 498
finalBatch = False
batchIndexStart = 0
batchIndexEnd = 0 + batchSize
batch = 0

# send of batch requests
while not finalBatch:

    # Check if we are on the final batch..
    # This is when the size of the next batch exceeds number of 
    # remaining dates
    if batchIndexEnd > len(dates): 

        batchIndexEnd = len(dates) -1 # Size the batch to match the no. remaining dates
        finalBatch = True # Signals to exit the while-loop
        # send off final batch
        ohlcvBatchDF = tickerInfo.history(start = dates[batchIndexStart],\
                                end = dataUntil, interval="1d")

    # This else handles all other full-size batchrequests
    else: 
        ohlcvBatchDF = tickerInfo.history(start = dates[batchIndexStart],\
                                        end = dates[batchIndexEnd], interval="1d")
        time.sleep(0.5)
    
    # Keep track of no. batches sent for record purposes
    batch = batch + 1
    
    logging.info("Normalising dates")
    # Convert date time in index to just date (time is not important)
    ohlcvBatchDF.index = ohlcvBatchDF.index.date
    # Move date out of index to a new column because it's awkward
    # for now.
    ohlcvBatchDF = ohlcvBatchDF.reset_index()
    ohlcvBatchDF.rename(columns={'index': 'Date'}, inplace=True)

    
    # Concatenate newest batch with previous batch in a dataframe
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

    # Some dates are missing because makrets aren't always open.
    datesSet = set(ohlcvDF["Date"])
    missingDates = []
    for date in dates:
        if not date in datesSet:
            missingDates.append(date)
    
    # Add these missing dates to the dataframe with NaN values
    for missingDate in missingDates:
        ohlcvDF.loc[len(ohlcvDF)] = {'Date': missingDate}
    
    # Sort dataframe so mdates are in order 
    ohlcvDF = ohlcvDF.sort_values(by='Date')
    ohlcvDF = ohlcvDF.ffill().reset_index(drop=True)
    
 
    # Now we remove the dates from the ticker dataframe that
    # are not matched with out btc data
    btcdataFromIndex = ohlcvDF.loc[ohlcvDF['Date']\
                                        == dataFrom].index[0]
    ohlcvDF = ohlcvDF.iloc[btcdataFromIndex:]
    ohlcvDF = ohlcvDF.reset_index(drop=True)

# Store data
if batch == 0: # If ticker data was already up to date...
   logging.info(f"{dataName} Data up to date. Nothing to be appended.")
elif not alreadyData: # If we are creating a new data set for our ticker
    logging.info(f"Sent off {batch} requests.")
    # create brand spanking new df
    ohlcvDF.to_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    logging.info(f"New data frame created from {str(len(ohlcvDF))} new data points and pickled.")
else: # else we are adding new data to an existing data set for our ticker
    logging.info(f"Sent off {batch} requests.")
    btcDataFrame = pd.concat([existingDataFrame, ohlcvDF], axis=0, ignore_index=True)
    # drop any duplicate rows based on the timestamp (just in case)
    btcDataFrame.drop_duplicates(subset='Date', keep='last', inplace=True)
    # Save the updated dataframe
    ohlcvDF.to_pickle(os.path.join(DATA_DIR, f"{dataName}_ohlcv_data.pkl"))
    logging.info(f"{str(len(ohlcvDF))} new data points downloaded.")
    logging.info("New data added to existing data frame.")


logging.info("S&P 500 Dataframe:")
logging.info(ohlcvDF)
logging.info("\n\nScript Complete!\n\n")