import datetime
import os
import logging

def unix_to_ymd(unixDate):
        timestamp = unixDate
        timestamp = timestamp / 1000
        date = datetime.datetime.fromtimestamp(timestamp).date()
        ymd = date.strftime('%Y-%m-%d')

        return ymd

def unix_to_ymdhms(unixDate):
        timestamp = unixDate
        timestamp = timestamp / 1000
        dateTime = datetime.datetime.fromtimestamp(timestamp)
        ymdhms = dateTime.strftime('%Y-%m-%d  %H:%M:%S')

        return ymdhms

    
def setup_logging(logDir):
    logFileName = 'log.txt'
    logName = os.path.join(logDir, logFileName)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[logging.FileHandler(logName),
                                  logging.StreamHandler()])
    

def save_plot(fig, filename, path):
    """
    mainly for saving plots to summary directories 
    """
    
    plot_file_path = os.path.join(path, filename)
    fig.savefig(plot_file_path)


def write_to_file(message, path):
    """
    mainly for saving analysis outputs to summary files 
    """
    # Convert message to string if it's not already
    if not isinstance(message, str):
        message = str(message)

    with open(path, 'a') as file:
        file.write(message + "\n")

