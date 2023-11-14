import pandas as pd
import sys
import os
import logging
import seaborn
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np



sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR, LOGS_DIR
from utilities import setup_logging
from utilities import save_plot

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
logging.info(f"Performing Multiple Regression Analysis post PCA.")
logging.info(f"--------------------------------------------\n\n")
#logging.info(f"\n\nStandard Errors are heteroscedasticity robust [HC3]\n")


# Check for PCA DF
try:
    dataFrame = pd.read_pickle(os.path.join(DATA_DIR, "post_pca_data.pkl"))

    logging.info("PCA data detected.")

except FileNotFoundError:
    logging.error("No PCA data detected. Cannot proceed.")
    sys.exit()

IVs = [col for col in dataFrame.columns[1:] if "BTC Price" not in col]


# Define the dependent and independent variables
X = dataFrame[IVs]
y = dataFrame['BTC Price']

# Add a constant to the model
X = sm.add_constant(X)

# Fit the model
#model = sm.OLS(y, X).fit()
# MUST USE TYPE HC3 due to blatant heteroscedacity!!!
model = sm.OLS(y, X).fit(cov_type='HC1')

# Print out the statistics
logging.info("Post PCA Multiple Regression Analysis Results:")
logging.info("\n")
logging.info(model.summary())

logging.info("Plotting data..")

# Residuals vs Fitted
plt.figure(figsize=(10, 5))
seaborn.residplot(x=model.fittedvalues, y=model.resid, lowess=True)
plt.axhline(y=0, color='grey', linestyle='dashed')
plt.xlabel('Fitted values')
plt.ylabel('Residuals')
plt.title('Post PCA Residuals vs Fitted')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "post_pca_residuals_vs_fitted_figure.png")

# QQ-Plot
plt.figure(figsize=(10, 5))
sm.qqplot(model.resid, line='s')  # s indicates standardized line
plt.title('Post PCA Normal Q-Q')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "post_pca_normal_q-q_plot.png")

# Standardized Residuals
plt.figure(figsize=(10, 5))
standardized_residuals = model.get_influence().resid_studentized_internal
plt.scatter(model.fittedvalues, standardized_residuals)
plt.axhline(y=0, color='grey', linestyle='dashed')
plt.xlabel('Fitted values')
plt.ylabel('Standardized Residuals')
plt.title('Post PCA Standardized Residuals')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "post_pca_standardised_residuals_plot.png")

# Leverage vs Standardized Residuals (Cook's Distance)
plt.figure(figsize=(10, 5))
influence = model.get_influence()
(c, p) = influence.cooks_distance
plt.stem(np.arange(len(c)), c, markerfmt=",")
plt.title('Post PCA Cooks distance plot')
plt.xlabel('Observation')
plt.ylabel('Cooks Distance')
# Save the plot
fig = plt.gcf()
save_plot(fig, logDir, "post_pca_cooks_distance_plot.png")

logging.info("Plots completed and saved.")
logging.info("\n\nScript Complete!\n\n")