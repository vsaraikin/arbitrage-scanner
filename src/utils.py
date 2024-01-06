import functools
import json
import time
from typing import Any, Callable

from src.const import PATH_TO_CONFIGS


def write_data(data: dict, filename: str) -> None:
    """Write data to json"""
    with open(filename, "w") as file:
        json.dump(data, file, sort_keys=True, indent=4, separators=(',', ': '))


def read_data(filename: str) -> Any | None:
    """Read data from json"""
    try:
        with open(filename, 'r') as file:
            file = json.load(file)
        return file
    except FileNotFoundError:
        return None


def read_configs():
    return read_data(PATH_TO_CONFIGS)


def timeit(func: Callable):
    """Decorator to track time of completion"""

    @functools.wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # first item in the args, ie `args[0]` is `self`
        print(f'Function {func.__name__} took {total_time:.4f} seconds')
        return result

    return timeit_wrapper
