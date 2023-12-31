# BTC_Analyser

Examines the influence of large amounts of economic data (debt, futures, interest, ETFs) on bitcoin Price.

First historic economic data and the price of BTC over time is downloaded.
The data is detrended following an Automated Dickie-Fuller test and a 
preliminary multiple regression analysis is performed. You will have the choice to manually detrend it or
allow it to be automatically detrended (recommended).

Pearsons correlation is then carried out and correlated variables are used in a principle component analysis.
This effectively accounts for the strong heteroscedacity of the data. 

A second round of multiple regression analyses are peformed on the new principle components and the detrended BTC price.
A range of lags from days, to weeks, to months are introduced to look for a delayed effect of the economic component
on BTC price. This may help identify which principle component and which lag settings are appropriate.

SARIMAX is then performed. Users are allowed to input specific p, q, and d values or use a range to look for the best
combination. Lag can also be introduced; if it is a forecast is generated lag-days into the future. The
optimisation method used is Broyden-Fletcher-Goldfarb-Shanno with a maximum of 500 iterations allowed
which is slow but the data is rich.

Each time the analyser runs it creates a dated log containing the details of the analysis. The log includes
plotted data and summaries of each step of the analysis. In `docs` there are some files to help the uninitiated
understand the outputs and graphs. These need updating.


_I would suggest at this current time that BTC prices cannot reliably be tracked using gross economic measures as I have here.
BTC has transitioned from a fringe ponzi-scheme to an asset of decreasing risk with high potential
yield, it has not therefore responded consistently to economic events over time. The type of investor
and their rationale for holding bitcoin will have changed extensively._
_(quality of this present analysis not-withstanding)._

_It would be pertinent to select and justify what economic measures I include to reduce nosie, e.g. by identifying metrics
that exhibit some relationship to BTC and only including those._


_____________________

High Priority:
 - Check it runs on other machines via `launch.bat`
 - Allow analysis to be run without requiring that data has to be updated.
 - Look into tranformations for kurtosis.
 - Change what economic factors go into the PCA.
 - Add more data such as unemployment data.
- Improve commenting and standardise script layouts. Bring closer to PEP-8.

_____________________

Wishful To Do:
- Download and analyse blockchain data for its own analysis.
- Provide report summarising forecasts based off of economic and blockchain data.

