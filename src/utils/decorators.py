import functools
import json
import time
from typing import Any, Callable


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
