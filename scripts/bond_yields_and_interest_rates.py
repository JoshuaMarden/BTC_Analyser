import quandl
import logging
import datetime
import time
import os
import sys
import pandas as pd


# !Note that the API limits are so lenient and the download so quick that 
# I don't do batch requesting, I just request the entire data set again.

# Yes I should probably not do this.

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR, LOGS_DIR
from utilities import setup_logging

apiKey = "XsGfKb9pLcyxBhB77Xm_" # QuandL API Key
# List data names and 'tickers'
dataNames = [["bonYieldData", "USTREASURY/YIELD", "US_bond_yields"],\
             ["inflationData", "USTREASURY/REALLONGTERM", "US_real_interest"]]

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
logging.info(f"Downloading Bond Yields and (real) Interest Rate data.")
logging.info(f"--------------------------------------------")
logging.info(f"This script downloads the full data set again, in-line with\n"\
             "the dates we have for BTC.\n")


# Call the function from utilities.py to setup logging
setup_logging(logDir)

# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    firstRow = BTCdataframe.iloc[0].tolist() # get first candle
    lastRow = BTCdataframe.iloc[-1].tolist() # get first candle

    logging.info("Historical BTC data detected.")
    logging.info(f"Date of first BTC record :   {firstRow[0]}")

except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()

# Loop through the data sets we want
for dataSet in dataNames:
  logging.info(f"Fetching data for {dataSet[2]}.")

  getFrom = datetime.datetime.strptime(firstRow[0], '%Y-%m-%d') # str to date necessary conversion
  getUntil = datetime.datetime.strptime(lastRow[0], '%Y-%m-%d') # str to date necessary conversion

  # Get data starting date 7 days before our BTC data start date in case
  # we have to forward fill data
  sevenDaysPrior = getFrom - datetime.timedelta(days=7) # So we can interpolate data


  # Actual request for data
  dataSetDF = quandl.get(dataSet[1], authtoken=apiKey, start_date = sevenDaysPrior)

  # this rests the index to be a normal index as God intended.
  # Dates in the index are now stored under 'index'
  dataSetDF = dataSetDF.reset_index()
  # 'index' renamed to 'Date'
  dataSetDF.rename(columns={'index': 'Date'}, inplace=True)

  # Get list of all dates that should be in our df
  dates = []
  workingDate = sevenDaysPrior
 
  delta = datetime.timedelta(days=1)
  while workingDate <= getUntil:
      dates.append(workingDate)
      workingDate += delta

  # Add the missing dates to the dataframe
  datesSet = set(dataSetDF["Date"])
  missingDates = []
  for date in dates:
      if not date in datesSet:
          missingDates.append(date)

  for missingDate in missingDates:
      dataSetDF.loc[len(dataSetDF)] = {'Date': missingDate}

  dataSetDF = dataSetDF.sort_values(by='Date')
  dataSetDF = dataSetDF.reset_index(drop=True)

 
  # Dataframe now contains all dates, some containing NaN
  # Now we must forward fill them
  dataSetDF = dataSetDF.ffill().reset_index(drop=True)


  # Now we remove the dates from before the first date 
  # of our btc data
  btcStartDateIndex = dataSetDF.loc[dataSetDF['Date']\
                                    == firstRow[0]].index[0]
  dataSetDF = dataSetDF.iloc[btcStartDateIndex:]
  dataSetDF = dataSetDF.reset_index(drop=True)
  
  dataSetDF.iloc[:, 1:] = dataSetDF.iloc[:, 1:].astype(float)


  dataSetDF.to_pickle(os.path.join(DATA_DIR, f"{dataSet[2]}_data.pkl"))
  logging.info(f"New data frame created for {dataSet[2]} (#{str(len(dataSetDF))} data points) and pickled.")
  time.sleep(2)

  logging.info("Just downloaded and pickled:")
  logging.info(dataSetDF)

logging.info("\n\nScript Complete!\n\n")