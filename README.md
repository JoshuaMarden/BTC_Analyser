# BTC_Analyser
Examines at the price of BTC and potentially influential macroeconomic metrics.

This is essentially a series of scripts which download historic economic data and the price of BTC.
Data is detrended and a multiple rgeression analysis is performed.

Pearsons correlation is carried out and correlated variables are used in a principled component analysis.
A seconds multiple regression analysis is peformed the remaning variables and new principle components.
This effectively accounts for the heteroscedacity of some of then data.

Each time the analyser runs it creates a log containing the details of the analysis. The log also includes
plotted data.

It will ask for user input, to determin at what threshold two independent variables are considered correlated
enough to be included in the PCA.
