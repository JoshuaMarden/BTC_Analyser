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
logging.info(f"--------------------------------------------\n\n")
logging.info(f"Standard Errors are heteroscedasticity robust [HC3]\n")


# Check for BTC data
try:
    dataFrame = pd.read_pickle(os.path.join(DATA_DIR, "detrended_data_frame.pkl"))

    logging.info("Detrended macroeconomic data detected.")

except FileNotFoundError:
    logging.error("No macroeconomic data detected. Cannot proceed.")
    sys.exit()

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
#model = sm.OLS(y, X).fit()
# MUST USE TYPE HC3 due to blatant heteroscedacity!!!
model = sm.OLS(y, X).fit(cov_type='HC3')

# Print out the statistics
print("Multiple Regression Analysis Results:\n\n")
logging.info(model.summary())

# Residuals vs Fitted
plt.figure(figsize=(10, 5))
seaborn.residplot(x=model.fittedvalues, y=model.resid, lowess=True)
plt.axhline(y=0, color='grey', linestyle='dashed')
plt.xlabel('Fitted values')
plt.ylabel('Residuals')
plt.title('Residuals vs Fitted')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "residuals_vs_fitted_figure.png")

# QQ-Plot
plt.figure(figsize=(10, 5))
sm.qqplot(model.resid, line='s')  # s indicates standardized line
plt.title('Normal Q-Q')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "normal_q-q_plot.png")

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
save_plot(fig, logDir, "standardised_residuals_plot.png")

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
save_plot(fig, logDir, "cooks_distance_plot.png")