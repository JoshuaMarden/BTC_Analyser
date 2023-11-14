import datetime
import time
import sys
import os
import pandas as pd
import numpy as np
import logging
from statsmodels.tsa.stattools import adfuller

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from config import LOGS_DIR

# need to change print to log commands
# hneed to add exceptions in case any dataframe is missing a datapoint and needs to be excluded


# Setup logging
timeExecuted = time.strftime("%Y%m%d_%H%M%S")
logName = os.path.join(LOGS_DIR, f'data_pre_processing_log_{timeExecuted}.txt')
# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(logName),
                              logging.StreamHandler()])

# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))

    logging.info("Historical BTC data detected.")

except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()

BTCDF = pd.DataFrame(BTCdataframe[["Date", "Close"]])
print("-----------")
print(BTCDF)
print(f"size BTC dataframe: {len(BTCDF)}")

logging.info("Organising data...")

# Create a dictionary to store your dataFrames
dataFrames = {}

# Iterate over the files in the pickle directory
for pickledFile in os.listdir(DATA_DIR):
    # Construct the full file path
    filePath = os.path.join(DATA_DIR, pickledFile)
    # Ensure that you're only processing .pkl files
    if os.path.isfile(filePath) and\
      pickledFile.endswith('.pkl') and\
        "yields" not in pickledFile and\
          "BTC" not in pickledFile and\
            "detrended" not in pickledFile:

        # Load the DataFrame from the pickle file
        tempDF = pd.read_pickle(filePath)

        # Use the fileName without extension as the key
        fileName = os.path.splitext(pickledFile)[0]
        # Store the DataFrame in the dictionary
        dataFrames[fileName] = tempDF


# Make sure dates are correctly formatted and used as index
BTCDF['Date'] = pd.to_datetime(BTCDF['Date'])
BTCDF['Date'] = BTCDF['Date'].dt.date
BTCDF.set_index("Date", inplace=True)

# Merge dfs
for fileName, dataFrame in dataFrames.items():
    
    print(f"----------> Processing: {fileName}")
    tempDF = dataFrame
    # Check if the DataFrame has a 'Close' column
    if "Close" in dataFrame.columns:  # Check for 'Close' in the column names
        print("ohlcv data")
        # Create a new DataFrame from the 'Close' column
        tempDF = pd.DataFrame(tempDF[["Date", "Close"]])
        tempDF.columns = ["Date", fileName]  # Rename the column to the filename
    
    print(tempDF)
    # Make sure dates are correctly formatted and use as index
    tempDF['Date'] = pd.to_datetime(tempDF['Date'])
    tempDF['Date'] = tempDF['Date'].dt.date
    tempDF.set_index("Date", inplace=True)

    # Merge current dataframe with main dataframe
    BTCDF = pd.concat([BTCDF, tempDF], axis = 1, join = 'inner')


for col in BTCDF.columns:
    
    colString = str(col)
    if "Close" == colString:
        colString = colString.replace("Close", "BTC Price")
    if "_ohlcv_data" in colString:
        colString = colString.replace("_ohlcv_data", " Price")
    if "_" in colString:
        colString = colString.replace("_", " ")
    BTCDF.rename(columns={col: colString}, inplace=True)





print("****")
print("BTC DF:")
print(BTCDF)

#string_entries = AdjustedDF['US_2y_10y_yield_curve_data'][AdjustedDF['US_2y_10y_yield_curve_data'].apply(lambda x: isinstance(x, str))]
#print(string_entries)
AdjustedDF = BTCDF

pd.set_option('display.max_rows', None)
logging.info("\n\nPerforming Augmented Dickey-Fuller Tests...")


# We now need to account for stationarity in the data


for col in BTCDF.columns:
    
    # Use ADF to check for staionarity
    logging.info(f"ADF test for: {col}")
    ADFResult = adfuller(BTCDF[col])
    critValue = ADFResult[4]['5%']
    logging.info(f"ADF Statistic for {col}: {ADFResult[0]:.3f}")
    logging.info(f"p-value for {col}: {ADFResult[1]:.3f}")
    logging.info(f"Critical Values for {col}: {ADFResult[4]}")
    
    # Setup vars for col naming
    logColName = f"{col} Log"
    cubeRootColName = f"{col} Cube Root"
    differencedLogColName = f"{col} Log Differenced"

    # Check for negative values in the column
    has_negative_values = (BTCDF[col] < 0).any() 
   
    if ADFResult[0] > critValue and not has_negative_values:
         
        # If unit roots (non-stationarity) detected and no-neg values,
        # we calculate the log and then the log difference
        # we add epsilon to 0 values to avoid div by zero errors

        print(f"ADF Statistic ({ADFResult[0]:.3f}) does not fall beneath the critical value at 5% ({critValue:.3f}).")
        print(f"p-value = {ADFResult[1]:.3f}")
        print("Performing logarithmic adjustment..\n")
        epsilon = 1e-9
        print("Calculating Log Values..")
        print([logColName])
        AdjustedDF[logColName] = np.log(AdjustedDF[col] + epsilon)
        print("Calculating Log Difference Values..")
        AdjustedDF[differencedLogColName] = AdjustedDF[logColName].diff()
        AdjustedDF = AdjustedDF.bfill()
    
    elif ADFResult[0] > critValue and has_negative_values:
        
        # If unit roots (non-stationarity) detected and negative values,
        # perform A cube root adjustment.
        # We must account for this after the regression!!
        
        print(f"ADF Statistic ({ADFResult[0]:.3f}) does not fall beneath the critical value at 5% ({critValue:.3f}).")
        print(f"p-value = {ADFResult[1]:.3f}")
        print("Performing cube-root adjustment..\n")

        AdjustedDF[cubeRootColName] = np.cbrt(AdjustedDF[col])

    else:    
        print(f"ADF Statistic ({ADFResult[0]:.3f}) falls beneath the critical value at 5% ({critValue:.3f}).")
        print(f"No adjustment needed.")
        print(f"p-value: {ADFResult[1]:.3f}")
        AdjustedDF[cubeRootColName] = np.cbrt(AdjustedDF[col])

# Display the adjusted DataFrame
#AdjustedDF.to_pickle(os.path.join(DATA_DIR, f"stationarity_adjusted_data_frame.pkl"))
logging.info(f"New adjusted data frame created and pickled.")
