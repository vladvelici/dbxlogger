import time

def stopwatch():
    start = time.time()
    return lambda: time.time()-start
