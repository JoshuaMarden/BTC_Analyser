import requests
import datetime
import time
import pandas as pd
import sys
import os
import logging
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from config import LOGS_DIR

# Setup logging
timeExecuted = time.strftime("%Y%m%d_%H%M%S")
logName = os.path.join(LOGS_DIR, f'US_debt_download_log_{timeExecuted}.txt')
# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(logName),
                              logging.StreamHandler()])

# Function to get debt for a specific date 
def getDebtForDate(date):
    url = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?filter=record_date:gte:{date}-01-01"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0] if 'data' in data and len(data['data']) > 0 else None
    else:
        print(f"Failed to retrieve data for {date}. Status code: {response.status_code}")
        return None
    
    time.sleep(0.2)

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
dataUntil= datetime.datetime.strptime(dataUntil, '%Y-%m-%d')
sevenDaysPrior = dataFrom - datetime.timedelta(days=7) # So we can interpolate data

startYear = dataFrom - relativedelta(years=1)
startYear = int(startYear.year)
endYear = int(dataUntil.year)
workingYear = startYear
yearsToFetch = []
while workingYear <= endYear:
    yearsToFetch.append(workingYear)
    workingYear += 1
print(yearsToFetch)

datesAndDebt = []
# Loop over the range of dates
for year in yearsToFetch:
    temp = getDebtForDate(year)
    datesAndDebt.append(temp)

print(datesAndDebt)

debtDF = pd.DataFrame(datesAndDebt, columns=['Date', 'Debt'])


# Now we have to interpolate the data 

# Get list of all dates that should be in our df
dates = []
workingDate = sevenDaysPrior
getUntil = dataSetDF['Date'].iloc[-1]


while workingDate <= getUntil:
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

# Dataframe now contains all dates, some containing NaN
# Now we must forward fill them
dataSetDF = dataSetDF.ffill()

# Now we remove the dates from before the first date 
# of our btc data
btcStartDateIndex = debtDF.loc[debtDF['Date']\
                                  == dataUntil[0]].index[0]
debtDF = debtDF.iloc[btcStartDateIndex:]

dataSetDF.to_pickle(os.path.join(DATA_DIR, f"{dataSet[2]}_data.pkl"))
logging.info(f"New data frame created for US debt (#{str(len(debtDF))} data points) and pickled.")
