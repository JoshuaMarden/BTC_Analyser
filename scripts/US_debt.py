import requests
import datetime
import pandas as pd
import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from utilities import setup_logging

# Setup logging
if len(sys.argv) > 1:
    logDir = sys.argv[1]
    print(f"log directory: {logDir}")
else:
    raise ValueError("The dated log directory was not provided as an argument.")
# Call the function from utilities.py to setup logging
setup_logging(logDir)

logging.info(f"--------------------------------------------")
logging.info(f"Downloading US debt data.")
logging.info(f"--------------------------------------------\n\n")
logging.info(f"\nThis script downloads in batches and only downloads new data\n"\
             "points added since last update, provded they match dates in the\n"\
             "BTC data set.\n")



# Check for BTC data
try:
    BTCdataframe = pd.read_pickle(os.path.join(DATA_DIR, "BTC_ohlcv_data.pkl"))
    
    dataFrom = BTCdataframe.iloc[0, 0] # First date that we have BTC data for
    dataUntil = BTCdataframe.iloc[-1, 0] # Most recent datre that we have BTC data for


    logging.info("Historical BTC data detected.")
    logging.info(f"Date of first BTC record :   {dataFrom}")
    logging.info(f"Most recent BTC timestamp:   {dataUntil}")

except FileNotFoundError:
    logging.error("No historical BTC data detected. Cannot proceed.")
    sys.exit()


# Get data starting date 7 days before our BTC data start date in case
# we have to forward fill data
dataFrom = datetime.datetime.strptime(dataFrom, '%Y-%m-%d')
dataFrom = dataFrom.date()

timedelta = datetime.timedelta(days=7)
sevenDaysPrior = dataFrom - timedelta # So we can interpolate data

dataUntil = datetime.datetime.strptime(dataUntil, "%Y-%m-%d")
dataUntil = dataUntil.date()


# Get data from API

# Base URL for Fiscal Data API
baseURL = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/'
# Endpoint for the "Debt to the Penny" dataset
endpoint = 'v2/accounting/od/debt_to_penny'

batchSize = 100

# Parameters for the API call
# You'll need to specify the date range you're interested in
params = {
    'format': 'json',       # Format of the response
    'sort': '-record_date', # Sort by record_date in descending order
    'page[number]': 1,      # Page number
    'page[size]': batchSize,      # Page size
    'filter': f'record_date:gte:{sevenDaysPrior}'  # date onwards
}


# Init list
datesAndDebt = []

logging.info(f"Sending JSON request for data from {sevenDaysPrior} in batches of {batchSize}")

pageNumber = 1
morePages = True

while morePages:
    # Set the current page number
    params['page[number]'] = pageNumber
    
    # Construct the full URL
    url = f"{baseURL}{endpoint}"
    
    # Make the API call
    response = requests.get(url, params=params)
    
    # Check if the call was successful
    if response.status_code == 200:
        # Parse the response JSON
        data = response.json()
        
        # Process and print the data
        for record in data.get('data', []): 
            tempList = [record.get('record_date'), record.get('debt_held_public_amt')]
            tempList[0] = datetime.datetime.strptime(tempList[0], "%Y-%m-%d")
            tempList[0] = tempList[0].date()
            datesAndDebt.append(tempList)
            #print(tempList)
        logging.info(f"Received page {pageNumber}")
        
        # Check if there is a next page
        # Adjust this based on the actual API response
        # Check for the presence of the 'next' link
        links = data.get('links', {})
        if links.get('next'):  # This checks if 'next' is not None and not an empty string
            pageNumber += 1  # There's a next page, so increment the page number
        else:
            break  # 'next' is None, which means we're on the last page

    else:
        logging.error(f"Failed to retrieve data: {response.status_code}, Response: {response.text}")
        morePages = False  # Stop the loop if an error occurred

# Store in dataframe
datesAndDebt = reversed(datesAndDebt)
debtDF = pd.DataFrame(datesAndDebt, columns=['Date', 'Debt'])

# Now we have to interpolate the data 

dates = []
#Start the search for dates before BTC start date in case the first
# date is missing and has to be interpolated
workingDate = sevenDaysPrior

# Get list of all dates that should be in our df
delta = datetime.timedelta(days=1)
while workingDate <= dataUntil:
    dates.append(workingDate)
    workingDate += delta

# Add the missing dates to the dataframe
datesSet = set(debtDF["Date"])
missingDates = []
for date in dates:
    if not date in datesSet:
        missingDates.append(date)


for missingDate in missingDates:
    debtDF.loc[len(debtDF)] = {'Date': missingDate}

debtDF = debtDF.sort_values(by='Date')
debtDF = debtDF.reset_index(drop=True)

# Dataframe now contains all dates, some containing NaN
# Now we must forward fill them
debtDF = debtDF.ffill().reset_index(drop=True)

# Now we remove the dates from before the first date 
# of our btc data
btcStartDateIndex = debtDF.loc[debtDF['Date']\
                                  == dataFrom].index[0]
debtDF = debtDF.iloc[btcStartDateIndex:]
debtDF = debtDF.reset_index(drop=True)

debtDF['Debt'] = debtDF['Debt'].astype(float)

debtDF.to_pickle(os.path.join(DATA_DIR, f"US_debt_data.pkl"))
logging.info(f"New data frame created for US debt (#{str(len(debtDF))} data points) and pickled.")
logging.info("Debt dataframe:")
logging.info(debtDF)
logging.info("\n\nScript Complete!\n\n")