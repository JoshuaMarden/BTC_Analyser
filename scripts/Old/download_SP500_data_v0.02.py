import yfinance as yahFin
import datetime
import time
import sys
import os
import pandas as pd
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from config import LOGS_DIR

dataName = "SP500"
ticker = "^GSPC" # ticker required


# Setup logging
timeExecuted = time.strftime("%Y%m%d_%H%M%S")
logName = os.path.join(LOGS_DIR, f'{dataName}_download_log_{timeExecuted}.txt')
# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(logName),
                              logging.StreamHandler()])


# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    lastRow = BTCdataframe.iloc[-1].tolist() # get last candle in 
    firstRow = BTCdataframe.iloc[0].tolist() # get first canle in F

    logging.info("Historical BTC data detected.")
    logging.info(f"Date of first BTC record :   {firstRow[0]}")
    logging.info(f"Most recent BTC timestamp:   {lastRow[0]}")


except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()


# Now we want the data for out ticker over the same period as we have 
# our BTC data.
# dates are not in the datatframe online so we need to get a list of the 
# dates we want and then send off for them in batches.

tickerInfo = yahFin.Ticker(ticker) # ticker required
dataFrom = (firstRow[0]) # defines time window start
dataUntil = (lastRow[0]) # defined time window until

ohlcvDF = pd.DataFrame()

logging.info(f"Gathering data for {dataName}...")
logging.info(f"Gathering data for range {dataFrom} : {dataUntil}")


# Turn date strings into date objects so we can interpolate the dates
# between them
startDate = datetime.datetime.strptime(dataFrom, "%Y-%m-%d").date()
endDate = datetime.datetime.strptime(dataUntil, "%Y-%m-%d").date()
# setup the time change/delta for each iteration
delta = datetime.timedelta(days=1)
workingDate = startDate
dates = []




# iterate through dates adding one each time
while workingDate <= endDate:
    dates.append(workingDate)
    workingDate += delta

print(dates[-1])

# Setup vars for batch requesting
batchSize = 498
finalBatch = False
batchIndexStart = 0
batchIndexEnd = 0 + batchSize
batch = 0

while not finalBatch:
    
    if batchIndexEnd > len(dates): # handles getting to end of date list 
        batchIndexEnd = len(dates) -1
        finalBatch = True
        currDate = datetime.date.today()
        # Have to do it this way because 'end' doesn't get the end date...
        #...and batch size may put 'end' in future
        ohlcvBatchF = tickerInfo.history(start = dates[batchIndexStart],\
                                end = currDate, interval="1d")
        time.sleep(1)

    else: # handles all other iterations
        ohlcvBatchF = tickerInfo.history(start = dates[batchIndexStart],\
                                        end = dates[batchIndexEnd], interval="1d")
        time.sleep(1)
    
    batch = batch + 1

    ohlcvDF = pd.concat([ohlcvDF, ohlcvBatchF], axis=0, ignore_index=False)
        
    logging.info(f"Batch {batch} received and stored for period: "\
                 f"{dates[batchIndexStart]} : {dates[batchIndexEnd]}")
    
    # Updates batch indicies for next batch request
    batchIndexStart = batchIndexStart + batchSize
    batchIndexEnd = batchIndexEnd + batchSize

logging.info("Normalising dates")
#Convert date time in index to just time
ohlcvDF.index = ohlcvDF.index.date
# Move date out of index to a new column because it's awkward
ohlcvDF = ohlcvDF.reset_index()
ohlcvDF.rename(columns={'index': 'Date'}, inplace=True)


# Get the from before the BTC start date, this in case
# the new data doesn't have a matching date (e.g. weekend / holiday) 
sevenDaysPrior = startDate - datetime.timedelta(days=7)
earlierDataDF = tickerInfo.history(start=sevenDaysPrior, end=startDate, interval="1d")
earlierDataDF.index = earlierDataDF.index.date
earlierDataDF = earlierDataDF.reset_index()
earlierDataDF.rename(columns={'index': 'Date'}, inplace=True)


logging.info("Interpolating missing data")

datesSet = set(ohlcvDF["Date"])
missingDates = []
for date in dates:
    if not date in datesSet:
        missingDates.append(date)

for missingDate in missingDates:
    ohlcvDF.loc[len(ohlcvDF)] = {'Date': missingDate}

ohlcvDF = ohlcvDF.sort_values(by='Date')


# Add earlier data above the dataframe in case the first data
# point needs interpolating
tempExtendedDF = pd.concat([earlierDataDF, ohlcvDF]).reset_index(drop=True)
# iterpolate the data by forward filling calls that contain NaN
# values 

print(ohlcvDF)
print("----------")


tempExtendedDF = tempExtendedDF.ffill()
# remove the excess data from the top of the dataframe
ohlcvDF = tempExtendedDF.iloc[7:, :-2]


pd.set_option('display.max_columns', None)
print(ohlcvDF)