# BTC_Analyser


Examines at the influence of large amounts of economic data (debt, futures, interest, ETFs) on bitcoin Price.

First historic economic data and the price of BTC over time is downloaded.
That data is detrended following an Automated Dickie-Fuller test and a 
preliminary multiple regression analysis is performed.

Pearsons correlation is then carried out and correlated variables are used in a principle component analysis.
A second multiple regression analysis is peformed on the new principle components.
This effectively accounts for the strong heteroscedacity of the data.

SARIMAX is then performed. WARNING SARIMAX does not currently take into account seasonality.
It cannot therefore forecast effectively.

Each time the analyser runs it creates a dated log containing the details of the analysis. The log includes
plotted data and summaries of each analysis. In `docs` there are some files to help the uninitiated
understand the outputs and graphs. These need updating.


_____________________

Immediate To Do:
 - Check it runs on other machines via `launch.bat`
 - Allow analysis to be run without requiring that data has to be updated.
 - Allow analysis to be re-run instead of just terminating so it's easier to try different
   settings.
- Add more options to configure analysis via user input.

_____________________

Wishful To Do:
- find a way to better remove seasonality and detrend data.
- add functional forecasting
- Download and analyse blockchain data for its own analysis.
- Provide report summarising forecasts based off of economic and blockchain data.

