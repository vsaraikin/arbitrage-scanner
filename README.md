# Cryptocurrency arbitrage scanner

Install requirements:

`pip install -r requirements.txt`

Run scanner:

`python main.py`


## How does scanner works?

1. Scrape all possible pairs in `tickers_exchanges.json`.
2. Match tickers with selected exchanges in `create_configs.py`.
3. Check if market is liquid.
   1. Create a DB to store checked pairs and attach a bool variable whether it is checked.
   2. There is a baseVolume key in watch_ticker method which we assign to bool variable. True if baseVolume 350k+
4. 