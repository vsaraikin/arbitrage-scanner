import json
from functools import wraps
import time
import requests as r
import pandas as pd
from random import choice


def write_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file)
        

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # first item in the args, ie `args[0]` is `self`
        print(f'Function {func.__name__} took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


def get_proxy(ssl):
    res = r.get('https://free-proxy-list.net/', headers={'User-Agent':'Mozilla/5.0'}).text
    table = pd.read_html(res)[0]
    if ssl:
        return choice(table[table['Https'] == 'yes']['IP Address'].to_list())
    else:
        return choice(table[table['Https'] == 'no']['IP Address'].to_list())
