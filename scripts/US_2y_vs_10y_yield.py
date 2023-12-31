import logging
import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR, LOGS_DIR
from utilities import setup_logging

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
logging.info(f"Calculating 2yr : 10yr Bond Yields.")
logging.info(f"--------------------------------------------")


# Check for bond yield data
try:
    yieldsDF = pd.read_pickle(os.path.join(DATA_DIR, "US_bond_yields_data.pkl"))

    logging.info("Yield data detected.")

except FileNotFoundError:
    logging.error("No yield data detected. Cannot proceed.")
    sys.exit()

yieldsDF['2y/10y Yield Spread (%)'] = (yieldsDF['10 YR'] - yieldsDF['2 YR']) * 100  # Multiply by 100 to convert to percentage
# Show the updated DataFrame



yieldCurveDF = yieldsDF.iloc[:, [0, -1]]
yieldCurveDF.iloc[:, -1] = yieldCurveDF.iloc[:, -1].astype(float)


yieldCurveDF.to_pickle(os.path.join(DATA_DIR, f"US_2y_10y_yield_curve_data.pkl"))
logging.info(f"Yield comparison completed and pickled.")

logging.info("2y/10y Bond Yield Spread (%) Dataframe\n\n")
logging.info(yieldCurveDF)
logging.info("\n\nScript Complete!\n\n")