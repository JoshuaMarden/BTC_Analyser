import pandas as pd
import sys
import os
import logging
import seaborn
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA as performPCA



sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATA_DIR, LOGS_DIR
from utilities import setup_logging, save_plot, write_to_file

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
logging.info(f"\n\nPerforming Pearson Correlation & Principle Component Analysis.\n")
logging.info(f"--------------------------------------------")
logging.info(f"\n\n")
# Check for BTC data
try:
    dataFrame = pd.read_pickle(os.path.join(DATA_DIR, "detrended_data_frame.pkl"))

    logging.info("Detrended macroeconomic data detected.")

except FileNotFoundError:
    logging.error("No macroeconomic data detected. Cannot proceed.")
    sys.exit()

# Make a specific log for thsi analysis
# then write to it using write to file
dirName = "pearsons_and_pca_summary"
# Full path for the new dated log directory
analysisSummaryDir = os.path.join(logDir, dirName)
# Create the dated log directory if it doesn't exist
os.makedirs(analysisSummaryDir, exist_ok=True)
# Full path for the new log file inside the dated log directory
summaryFilePath = os.path.join(analysisSummaryDir, 'multiple_regression_analysis.txt')
msg = "This file contains the summary of the Pearson's correlation\n\
       and the Principle component analysis.\n\n\
       For help understanding this summary look in the docs file.\n\n"
write_to_file(msg, summaryFilePath)

# Pearsons correlation

tempDF = dataFrame.copy()
# Iterate over the columns and remove those that don't contain "trend"
for col in tempDF.columns:
    colString = str(col)
    if "rend" not in col:
        tempDF.drop(col, axis=1, inplace=True)

# Rename the columns by removing " Detrended" or " No Trend"
tempDF.columns = [col.replace(" Detrended", "").replace(" No Trend", "") for col in tempDF.columns]

# Create matrix
correlationMatrix = tempDF.corr(method='pearson')
logging.info("\nGenerating correlation matrix.\n")
logging.info(correlationMatrix)
# Create plot of matrix
seaborn.heatmap(correlationMatrix, annot=True)
plt.title("Correlation Matrix of Independent Variables")
plt.tight_layout()

# save the plot and save the data
save_plot(plt, "correlation_matrix_plot.png", analysisSummaryDir)
correlationMatrix.to_pickle(os.path.join(DATA_DIR, "pearson_correlation_matrix.pkl"))
logging.info("\nCorrelation matrix saved to data, plot saved in logs.\n")
msg = "Pearsons Correlation Matrix"
write_to_file(msg, summaryFilePath)
write_to_file(correlationMatrix, summaryFilePath)
write_to_file("\n", summaryFilePath)

# Prep data for PCA

# Identify strongly correlated pairs
print("Please see docs for understanding and chosing a threshold.")
print("The relevant correlation matrix is stored in the most recent log in:")
print(f"{logDir}")
userInput = input("Chose a correlation threshold (default 0.5): \n\n")
# Check if the user has entered a value, if not, use the default value
try:
    threshold = float(userInput) if userInput else 0.5
except ValueError:
    print("Invalid input. Using default threshold of 0.5.")
    threshold = 0.5

logging.info(f"Variables exceeding correlation threshold {threshold}\n\
              will be included in PCA!\n")


strongCorrelations = np.where(np.abs(correlationMatrix) > threshold)
strongCorrelations = [(correlationMatrix.columns[x], correlationMatrix.columns[y])\
                      for x, y in zip(*strongCorrelations) if x != y and x < y]

# Extract unique variables from these pairs
colsToInclude = set([var for pair in strongCorrelations for var in pair])

# Exclude columns that contain "BTC" (our DV)
colsToInclude = [col for col in colsToInclude if "BTC" not in col]

logging.info("Variable pairs included in PCA:\n")
for i in colsToInclude:
    logging.info(F"{i}")


# Filter the DataFrame
filteredData = dataFrame[list(colsToInclude)]

# Standardize the data
scaler = StandardScaler()
scaledData = scaler.fit_transform(filteredData)


# Run PCA
logging.info("\n\nRunning PCA..\n")

# Perform PCA
pca = performPCA(n_components=0.95)  # Retain x% of the variance or specify n_components as an integer
principalComps = pca.fit_transform(scaledData)

# Find out the number of components
numComponents = pca.n_components_

# Create column names based on the number of components
colNames = [f'Economic Component{i+1}' for i in range(numComponents)]

# Convert to a DataFrame
PCADF = pd.DataFrame(data=principalComps, columns=colNames)

# Evaluate results
logging.info("\n\nVariance explained by each component:")
write_to_file("Variance explained by each component:", summaryFilePath)
for index, variance in enumerate(pca.explained_variance_ratio_):
    componentInfo = f"Principal Component {index + 1}: {variance:.4f}"
    logging.info(componentInfo)
    write_to_file(componentInfo, summaryFilePath)

# Store data for use in regression analysis
logging.info("\n\nSaving data PCA..\n")

# Remove the columns used in PCA from tempDF
tempDF.drop(columns=colsToInclude, inplace=True)

# Append PCA result (PCADF) to tempDF
if len(tempDF) == len(PCADF):
    # Assign the index of tempDF to PCADF
    PCADF.index = tempDF.index
    # Concat
    postPCADF = pd.concat([tempDF, PCADF], axis=1)
else:
    # Handle the discrepancy in row count
    raise ValueError("Row counts of tempDF and PCADF do not match.")

postPCADF.to_pickle(os.path.join(DATA_DIR, "post_pca_data.pkl"))
logging.info('PCA dataframe saved:')
logging.info(postPCADF)
logging.info('Plotting data..')

# Plot some of the outputs
# Scree Plot
plt.figure(figsize=(10, 6))
plt.plot(range(1, len(pca.explained_variance_ratio_) + 1), pca.explained_variance_ratio_, marker='o')
plt.title('Scree Plot')
plt.xlabel('Principal Component')
plt.ylabel('Variance Explained')
plt.xticks(range(1, len(pca.explained_variance_ratio_) + 1))
save_plot(plt, "pca_scree_plot.png", analysisSummaryDir)
logging.info('PCA scree plot saved.')

# Biplot
scores = pca.transform(scaledData)  # This line was missing
fig, ax = plt.subplots(figsize=(12, 6))
ax.scatter(scores[:, 0], scores[:, 1])
for i in range(pca.components_.shape[1]):
    ax.arrow(0, 0, pca.components_[0, i], pca.components_[1, i], head_width=0.05, head_length=0.05)
    ax.text(pca.components_[0, i] * 1.15, pca.components_[1, i] * 1.15, filteredData.columns[i], color='red')
save_plot(fig, "pca_biplot_plot.png", analysisSummaryDir)
logging.info('PCA Biplot saved.')

# Component Loadings Plot
fig, ax = plt.subplots(figsize=(12, 6))
for i in range(pca.components_.shape[1]):
    ax.arrow(0, 0, pca.components_[0, i], pca.components_[1, i], head_width=0.05, head_length=0.05)
    ax.text(pca.components_[0, i] * 1.15, pca.components_[1, i] * 1.15, filteredData.columns[i], color='red')
save_plot(fig, "pca_components_loading_plot.png", analysisSummaryDir)
logging.info('PCA Components Loading Plot saved.')

# plt.xlabel('PC1')
# plt.ylabel('PC2')
# plt.title('Component Loadings Plot')
# plt.grid()
# save_plot(plt, logDir, "pca_component_loadings_plot.png")
# logging.info('\nPCA Component Loadings Plot saved.\n')


# plt.xlabel('PC1')
# plt.ylabel('PC2')
# plt.title('Biplot')
# plt.grid()
# save_plot(plt, logDir, "pca_biplot.png")
# logging.info('\nPCA Biplot saved.\n')

# # PCA Score Plot
# plt.figure(figsize=(12, 6))
# plt.scatter(principalComponents[:, 0], principalComponents[:, 1])
# plt.xlabel('PC1')
# plt.ylabel('PC2')
# plt.title('PCA Score Plot')
# plt.grid()
# save_plot(plt, logDir, "pca_score_plot.png")
# logging.info('\nPCA Score Plot saved.\n')

logging.info("\n\nScript Complete!\n\n")