import threading
import _thread
import time

# class timeout():
#   def __init__(self, time):
#     self.time= time
#     self.exit=False

#   def __enter__(self):
#     threading.Thread(target=self.callme).start()

#   def callme(self):
#     time.sleep(self.time)
#     if self.exit == False:
#        _thread.interrupt_main()  # use thread instead of _thread in python2
       
#   def __exit__(self, *args):
#        self.exit=True

# from tqdm import tqdm

# def func():
#     return {x for x in tqdm(range(1000000))}

# with timeout(4):
#     print("abc")
#     func()

# ---------------------------

# class TimeoutError(Exception):
#     pass

# Works on UNIX
# def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
#     def decorator(func):
#         if not hasattr(signal, 'SIGALRM'):
#             return func
        
#         def _handle_timeout(signum, frame):
#             raise TimeoutError(error_message)

#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             signal.signal(signal.SIGALRM, _handle_timeout)
#             signal.alarm(seconds)
#             try:
#                 result = func(*args, **kwargs)
#             finally:
#                 signal.alarm(0)
#             return result

#         return wrapper

#     return decorator



# def someloop():
#     while 1:
#         print('aa')
#         time.sleep(1)
        
from eventlet.timeout import with_timeout
import urllib.request

def func():
    {x for x in range(100000000)}
    return 

data = with_timeout(0.1, func)
print(data)