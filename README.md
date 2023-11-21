# BTC_Analyser

***
Just updated to include more data, SARIMAX forecasting. NOt stable.
***
Examines at the influence of large amounts of economic data (debt, futures, interest, ETFs) on bitcoin Price.

First historic economic data and the price of BTC over time is downloaded.
That data is detrended following an Automated Dickie-Fuller test and a 
preliminary multiple regression analysis is performed.

DO NOT EXCLUDE DATA THAT FAILS DETRENDING - before SARIMAX it all does.

Pearsons correlation is then carried out and correlated variables are used in a principle component analysis.
A second multiple regression analysis is peformed on the new principle components.
This effectively accounts for the strong heteroscedacity of the data.

SARIMAX with fixed parameters (for now) along with a forecast is performed. Forecast predicts BTC price following a 
30% increase or 30% decrease in current economic conditions.

Each time the analyser runs it creates a dated log containing the details of the analysis. The log includes
plotted data and summaries of each analysis. In `docs` there are some files to help the uninitiated
understand the outputs and graphs. These need updating.

User input is requested to at various points (DO NOT EXCLUDE DATA THAT FAILS DETRENDING - before SARIMAX it all does.)

_____________________

Immediate To Do:
 - Check it runs on other machines via `launch.bat`
 - Allow analysis to be run without requiring that data has to be updated.
 - Allow analysis to be re-run instead of just terminating so it's easier to try different
   settings.
- Add more options to configure analysis via user input.

_____________________

Wishful To Do:
- Add ARIMA and forecasting.
- Add more economic data to PCA, e.g. Gold Prices, Employment.
- Download and analyse blockchain data for its own analysis.
- Provide report summarising forecasts based off of economic and blockchain data.

