import json
from functools import wraps
import time
import requests as r
import pandas as pd
from termcolor import cprint
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector

    
def write_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file)
        
        
def read_data(filename):
    with open(filename, 'r') as file:
        file = json.load(file)
        
    return file
        

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


def get_proxy(ssl, url):
    res = r.get(url, headers={'User-Agent':'Mozilla/5.0'}).text
    table = pd.read_html(res)[0]
    table['IP'] = table['IP Address'].apply(str) + ':' +  table['Port'].apply(str)
    cprint('Requested more proxies', 'yellow')
    if ssl:
        return table[table['Https'] == 'yes']['IP'].to_list()
    else:
        return table[table['Https'] == 'no']['IP'].to_list()

    

@timeit
def generate_proxies():
    
    timeout = 2
    
    async def check(socket_address: str, proto: str) -> None:
        proxy_url = f"{proto}://{socket_address}"
        async with ProxyConnector.from_url(proxy_url) as connector:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                try:
                    response = await session.get("http://ip-api.com/json/?fields=8217",timeout=timeout,raise_for_status=True,)
                    data = await response.json()
                    await session.close()
                    geolocation = "|{}|{}|{}".format(
                        data["country"], data["regionName"], data["city"]
                    )
                    cprint(geolocation, 'yellow')
                    return socket_address
                
                except Exception as e:
                    await session.close()
                    # print(e)

    async def generate_with_proto(proto: str) -> str:

            if proto == 'https':
                while True:
                    https_proxy_list = get_proxy(ssl=True, url='https://www.sslproxies.org/')
                    tasks = [asyncio.ensure_future(check(proxy_ip, 'http')) for proxy_ip in https_proxy_list]
                    
                    for coro in asyncio.as_completed(tasks):
                        result = await coro
                        if isinstance(result, str):
                            del tasks # the same as loop.stop() but without errors
                            return result
                    
            elif proto == 'http':
                while True:
                    http_proxy_list = get_proxy(ssl=False, url='https://free-proxy-list.net/')
                    tasks = [asyncio.ensure_future(check(proxy_ip, 'http')) for proxy_ip in http_proxy_list]
                    
                    for coro in asyncio.as_completed(tasks):
                        result = await coro
                        if isinstance(result, str):
                            del tasks # the same as loop.stop() but without errors
                            return result
                        
            else:
                raise ValueError("Unknown proto type")

    http_proxy = asyncio.run(generate_with_proto('http'))
    https_proxy = asyncio.run(generate_with_proto('https'))
    
    if http_proxy and https_proxy:
        return (http_proxy, https_proxy)
    else:
        exit()
    
