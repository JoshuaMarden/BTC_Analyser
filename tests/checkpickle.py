import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR

try:
    ohlcvDataframe = pd.read_pickle(os.path.join(DATA_DIR, "ohlc_data.pkl"))
    print("Historical data detected...")

    readableDataframe = ohlcvDataframe.copy()
    readableDataframe['timestamp'] = pd.to_datetime(ohlcvDataframe['timestamp'], unit='ms')
    print(readableDataframe)

except:

    print("No data found")