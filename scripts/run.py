import os
import sys
import datetime
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import LOGS_DIR

def createDatedLogDir():
    # Get the current date and time formatted as 'YYYY-MM-DD_HH-MM-SS'
    currTime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create a folder name with the current date and time
    dirName = f"log_for_{currTime}"
    # Full path for the new dated log directory
    datedLogDir = os.path.join(LOGS_DIR, dirName)
    # Create the dated log directory if it doesn't exist
    os.makedirs(datedLogDir, exist_ok=True)
    # Full path for the new log file inside the dated log directory
    logFilePath = os.path.join(datedLogDir, 'log.txt')
    # Create and open a log file in write mode within the new directory
    with open(logFilePath, 'w') as logFile:
        logFile.write(f"Log created on {currTime}\n")
    # Return the paths to the new log directory and log file
    print(f"dated log: {datedLogDir}")
    return datedLogDir

# Function to run scripts and pass the log directory and log file as arguments
def runScripts(datedLogDir):
    # List of scripts to run in order
    scriptsInOrder = [
        "download_BTC_data.py",
        "download_SP500_data.py",
        "bond_yields_and_interest_rates.py",
        "US_2y_vs_10y_yield.py",
        "US_debt.py",
        "detrending.py",
        "multiple_regression_analaysis.py",
        "pearsons_correlations_and_pca.py",
        "post_pca_multiple_regression_analaysis.py"
        ]
    

    # Run each script in the list
    for script in scriptsInOrder:
        # Construct the command to run the script with arguments
        command = ['python', script, datedLogDir]
        # Run the command and wait for it to complete
        subprocess.run(command, check=True)


# Function to ask for user input to continue
def requireInput():
    input("Press Enter to run the scripts or Ctrl+C to cancel...")

# Main function to coordinate the process
def main():

    # Ask for user input to proceed
    requireInput()
    # Create a log folder for the current run
    datedLogDir = createDatedLogDir()
    # Run the scripts with the log folder as an argument
    runScripts(datedLogDir)
    print(f"All scripts have been run. Logs and figures saved in: {datedLogDir}")

if __name__ == "__main__":
    main()