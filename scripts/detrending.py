import datetime
import time
import sys
import os
import pandas as pd
import numpy as np
import logging
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.stattools import adfuller

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from utilities import setup_logging
from utilities import save_plot


# need to add exceptions in case any dataframe is missing a datapoint and needs to be excluded
# adding lag to this model provided no useful insights. 
 
# Setup logging
if len(sys.argv) > 1:
    logDir = sys.argv[1]
    print(f"log directory: {logDir}")
else:
    raise ValueError("The dated log directory was not provided as an argument.")
# Call the function from utilities.py to setup logging
setup_logging(logDir)

logging.info(f"\n\nDetrending data.\n")
logging.info(f"\nData trends must be removed prior to multiple regression"\
             "analaysis.\n")


# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))

    logging.info("Historical BTC data detected.")

except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()

BTCDF = pd.DataFrame(BTCdataframe[["Date", "Close"]])
logging.info("Dataframe: ")
logging.info(BTCDF)
logging.info(f"size BTC dataframe: {len(BTCDF)}")

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
            "detrended" not in pickledFile and\
                "pearson" not in pickledFile and\
                    "pca" not in pickledFile:

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
    
    print(f"\n\n----------> Processing: {fileName}\n")
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

adjustedDF = BTCDF

logging.info("\n\nPerforming Augmented Dickey-Fuller Tests...\n\n")

# We now need to account for stationarity in the data

for col in BTCDF.columns:
    
    # Use ADF to check for staionarity
    logging.info(f"\n\nADF test for: {col}\n")
    ADFResult = adfuller(BTCDF[col])
    critValue = ADFResult[4]['5%']
    logging.info(f"ADF Statistic for {col}: {ADFResult[0]:.3f}")
    logging.info(f"p-value for {col}: {ADFResult[1]:.3f}")
    logging.info(f"Critical Values for {col}: {ADFResult[4]}")
    
    # Setup vars for col naming
    detrendedColName = f"{col} Detrended"
   
    if ADFResult[0] > critValue:

        print(f"ADF Statistic ({ADFResult[0]:.3f}) does not fall beneath the critical value at 5% ({critValue:.3f}).")
        print(f"p-value = {ADFResult[1]:.3f}")
        print("Detrending..\n")
        adjustedDF[detrendedColName] = signal.detrend(adjustedDF[(col)])        
    
    else:    
        print(f"ADF Statistic ({ADFResult[0]:.3f}) falls beneath the critical value at 5% ({critValue:.3f}).")
        print(f"No adjustment needed.")
        print(f"p-value: {ADFResult[1]:.3f}")

adjustedDF.index = pd.to_datetime(adjustedDF.index)
adjustedDF.to_pickle(os.path.join(DATA_DIR, f"detrended_data_frame.pkl"))
logging.info(f"New adjusted data frame created and pickled.")

# Plotting Data

# Count the number of detrended columns
num_detrended_cols = sum('Detrended' in col for col in adjustedDF.columns)

# Create subplots based on the number of detrended columns
fig, axes = plt.subplots(nrows=num_detrended_cols, ncols=2, figsize=(14, 7 * num_detrended_cols), sharex=True)

# Flatten the axes array for easy iteration if it's multidimensional
axes = axes.flatten() if num_detrended_cols > 1 else [axes]

# Track the current subplot index
subplot_index = 0

# Loop through the columns and plot the original and detrended data side by side
for col in adjustedDF.columns:
    if 'Detrended' in col:
        original_col = col.replace(' Detrended', '')

        # Plot the original data
        axes[subplot_index].plot(adjustedDF.index, adjustedDF[original_col], label=original_col, color='tab:blue')
        axes[subplot_index].legend()
        subplot_index += 1

        # Plot the detrended data
        axes[subplot_index].plot(adjustedDF.index, adjustedDF[col], label=col, color='tab:orange')
        axes[subplot_index].legend()
        subplot_index += 1

for ax in axes:
    ax.xaxis.set_major_locator(mdates.YearLocator())  # Locate ticks every year
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  # Format ticks as years

for ax in axes[:-2]:
    plt.setp(ax.get_xticklabels(), visible=False)


# Adjust the layout
plt.tight_layout()
plt.subplots_adjust(bottom=0.04)

# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "detrended_data_plots.png")
