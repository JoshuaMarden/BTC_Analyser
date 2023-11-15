import pandas as pd
import sys
import os
import logging
import seaborn
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np



sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR
from utilities import setup_logging
from utilities import save_plot
from utilities import write_to_file

# Setup logging
if len(sys.argv) > 1:
    logDir = sys.argv[1]
    print(f"log directory: {logDir}")
else:
    raise ValueError("The dated log directory was not provided as an argument.")
# Call the function from utilities.py to setup logging
setup_logging(logDir)

logging.info(f"--------------------------------------------")
logging.info(f"Performing Multiple Regression Analysis")
logging.info(f"--------------------------------------------")
logging.info(f"Standard Errors are heteroscedasticity robust [HC3]\n")


# Check for BTC data
try:
    dataFrame = pd.read_pickle(os.path.join(DATA_DIR, "detrended_data_frame.pkl"))

    logging.info("Detrended macroeconomic data detected.")

except FileNotFoundError:
    logging.error("No macroeconomic data detected. Cannot proceed.")
    sys.exit()

# Make a specific log for thsi analysis
# then write to it using write to file
dirName = "mra_summary"
# Full path for the new dated log directory
analysisSummaryDir = os.path.join(logDir, dirName)
# Create the dated log directory if it doesn't exist
os.makedirs(analysisSummaryDir, exist_ok=True)
# Full path for the new log file inside the dated log directory
summaryFilePath = os.path.join(analysisSummaryDir, 'multiple_regression_analysis.txt')
msg = "This file contains the summary of the multiple regression analysis\n\
       carried out on the economic data after it was detrended but before\n\
       a principle component analysis was perfomed to account for heteroscedacity.\n\n\
       Note that here covariance matrix estimator 'HC3', the most strict, was used to\n\
       try to make some modest adjustment for hetereoscedacity.\n\n\
       For help understanding this summary look in the docs file.\n\n"
write_to_file(msg, summaryFilePath)

IVs = []
for col in dataFrame.columns[1:]:
    if "Detrended" in col:
        IVs.append(col)
IVs = [i for i in IVs if "BTC Price" not in i]



# Define the dependent and independent variables
X = dataFrame[IVs]
y = dataFrame['BTC Price Detrended']

# Add a constant to the model
X = sm.add_constant(X)

# Fit the model
# MUST USE TYPE HC3 due to flagrant heteroscedacity!!!
model = sm.OLS(y, X).fit(cov_type='HC3')

# Print out the statistics
logging.info("Multiple Regression Analysis Results:\n\n")
logging.info(model.summary())
write_to_file(model.summary(), summaryFilePath)
logging.info("Saving plots...")

# Residuals vs Fitted
plt.figure(figsize=(10, 5))
seaborn.residplot(x=model.fittedvalues, y=model.resid, lowess=True)
plt.axhline(y=0, color='grey', linestyle='dashed')
plt.xlabel('Fitted values')
plt.ylabel('Residuals')
plt.title('Residuals vs Fitted')
# Save the plot
fig = plt.gcf()
save_plot(fig, "residuals_vs_fitted_figure.png", analysisSummaryDir)

# QQ-Plot
plt.figure(figsize=(10, 5))
sm.qqplot(model.resid, line='s')  # s indicates standardized line
plt.title('Normal Q-Q')
# Save the plot
fig = plt.gcf()
save_plot(fig, "normal_q-q_plot.png", analysisSummaryDir)

# Standardized Residuals
plt.figure(figsize=(10, 5))
standardized_residuals = model.get_influence().resid_studentized_internal
plt.scatter(model.fittedvalues, standardized_residuals)
plt.axhline(y=0, color='grey', linestyle='dashed')
plt.xlabel('Fitted values')
plt.ylabel('Standardized Residuals')
plt.title('Standardized Residuals')
# Save the plot
fig = plt.gcf()
save_plot(fig, "standardised_residuals_plot.png", analysisSummaryDir)

# Leverage vs Standardized Residuals (Cook's Distance)
plt.figure(figsize=(10, 5))
influence = model.get_influence()
(c, p) = influence.cooks_distance
plt.stem(np.arange(len(c)), c, markerfmt=",")
plt.title('Cooks distance plot')
plt.xlabel('Observation')
plt.ylabel('Cooks Distance')
# Save the plot
fig = plt.gcf()
save_plot(fig, "cooks_distance_plot.png", analysisSummaryDir)