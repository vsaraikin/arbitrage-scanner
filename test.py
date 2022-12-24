import ccxt.pro
from ticker_engineering.tools import generate_proxies


proxy = generate_proxies()

ex = ccxt.pro.binance({
    'proxies': {
        'http': 'http://10.10.1.10:3128',  # no auth
        'https': 'https://user:password@10.10.1.10:1080',  # with auth
    }
})
ex