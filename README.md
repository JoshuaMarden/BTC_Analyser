# BTC_Analyser
Examines at the influence of US Debt, US Inflation, US Bond Yield, US Interest Rates on BTC Price.

This is essentially a series of scripts which download historic economic data.
That data is detrended following an Automated Dickie-Fuller test and a 
preliminary multiple regression analysis is performed.

Pearsons correlation is then carried out and correlated variables are used in a principle component analysis.
A second multiple regression analysis is peformed on the new principle components.
This effectively accounts for the heteroscedacity of some of the data.

Each time the analyser runs it creates a log containing the details of the analysis. The log also includes
plotted data. In Docs there are some files to help the uninitiated understand the outputs and graphs.

User input is requested to determin at what threshold independent variables are considered correlated
enough to be included in the PCA.

_____________________

Immediate To Do:
 - Allow analysis to be run without checking for data to download
 - Allow analysis to be re-run instead of just terminating so it's easier to try different
   settings
- Add more options to configure analysis via user input

_____________________

Wishful To Do:
- Add ARIMA and forecasting 
- Add more economic data to PCA, e.g. Gold Prices, Employment
- Download and analyse blockchain data for its own analysis
- Provide report summarising forecasts based off of economic and blockchain data

