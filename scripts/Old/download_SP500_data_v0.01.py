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
from utilities import unix_to_ymd
from utilities import unix_to_ymdhms

# Setup logging
timeExecuted = time.strftime("%Y%m%d_%H%M%S")
logName = os.path.join(LOGS_DIR, f'SP500_download_log_{timeExecuted}.txt')
# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(logName),
                              logging.StreamHandler()])


# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    lastRow = BTCdataframe.iloc[-1].tolist() # get last candle in df
    firstRow = BTCdataframe.iloc[0].tolist() # get first canle in df

    logging.info("Historical BTC data detected.")
    logging.info(f"Most recent BTC timestamp:   {unix_to_ymdhms(int(lastRow[0]))}")


except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()




SP500Info = yahFin.Ticker("^GSPC") # ticker required
dataFrom = unix_to_ymd(firstRow[0]) # defines time window
dataUntil = unix_to_ymd(lastRow[0]) # ^
dataUntilBatch = dataUntil # required while req'ing batches
collectionComplete = False # loop stop sending requests when True

SP500Dataframe = pd.DataFrame()

logging.info("Gathering SP500 data...")
logging.info(f"Gathering data for range {dataFrom} : {dataUntil}")
batch = 0
# Get data in  yearly batches.
while not collectionComplete:
    
    print("-----")
    print(dataUntil)
    print("-----")
    
    # Takes the date of first BTC price in database...
    #...adds one to the year and changes date to Jan 1st...
    #...then requests data from BTCDataStart --> 01/01/YYY+1...
    #...loop then repeats gathering data until year after...
    #...01/01/YYYY+1 --> 01/01/YYY+2
    # On the final leg of the data it uses the correct end date...
    #...01/01/YYYY+x --> DataEnd
    
    
    if SP500Dataframe.empty == True:
        # Create 01/01 date to get data until 
        subsequentYear = str(int(dataFrom[0:4]) + 1)
        dataUntilBatch = subsequentYear + "-01-01" + dataFrom[10:]
        # Request that data for that time window
        ohlcvBatchDf = SP500Info.history(start = dataFrom, end = dataUntilBatch, interval="1d")
        batch = batch + 1
        # Concatenate that new data segment to the local dataframe
        SP500Dataframe = pd.concat([SP500Dataframe, ohlcvBatchDf], axis=0, ignore_index=True)
        
        logging.info(f"Batch {batch} received and stored for period: "\
                     f"{dataFrom[0:11]} + {dataUntil[0:11]}")
        
        # Set starting date for the next data request
        dataFrom = dataUntilBatch
        # Don't overwhelm server
        time.sleep(1)
      
    
    # If not in final year of BTC data
    elif not dataUntilBatch[0:4] == dataUntil[0:4]:
        # Create next 01/01 date to get data until 
        subsequentYear = str(int(dataFrom[0:4]) + 1)
        dataUntilBatch = subsequentYear + dataFrom[4:]
        # Request data for next time window - size of 365 days (01/01 -> 01/01)
        ohlcvBatchDf = SP500Info.history(start = dataFrom, end = dataUntilBatch, interval="1d")
        batch = batch + 1
        # Concatenate that new data segment to the local dataframe
        SP500Dataframe = pd.concat([SP500Dataframe, ohlcvBatchDf], axis=0, ignore_index=True)

        logging.info(f"Batch {batch} received and stored for period: "\
                     f"{dataFrom[0:11]} + {dataUntil[0:11]}")
        
        # Set starting date for the next data request
        dataFrom = dataUntilBatch
        # Don't overwhelm server
        time.sleep(1)
    
    else:
        # get last data segment
        ohlcvBatchDf = SP500Info.history(start = dataFrom, end = dataUntil, interval="1d")
        batch = batch + 1
        # Concatenate to the local dataframe
        SP500Dataframe = pd.concat([SP500Dataframe, ohlcvBatchDf], axis=0, ignore_index=True)
        logging.info(f"Final batch ({batch}) received and stored for period: "\
                     f"{dataFrom[0:11]} + {dataUntil[0:11]}")
        
        collectionComplete = True


# The dates aren't in the dataframe they need to be added...

# Turn date strings into date objects
startDate = datetime.datetime.strptime(dataFrom, "%Y-%m-%d").date()
endDate = datetime.datetime.strptime(dataUntil, "%Y-%m-%d").date()

delta = datetime.timedelta(days=1)
workingDate = startDate
dates = []

while workingDate <= endDate:
    dates.append(workingDate)
    workingDate += delta

print(dates)

print(SP500Dataframe)