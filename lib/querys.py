#querys.py
import subprocess

def _retry_check_output(*args, **kargs):
    """Same as subprocess.check_output, but tries not to take no for an answer."""
    retries = 5
    while retries:
        retries-=1
        try:
            return subprocess.check_output(*args, **kargs)
        except BlockingIOError: #swollow blocking errors and retry, but still fail on subprocess.TimeoutExpired errors
            time.sleep(.01)
            continue

def get_host_ip():
    """Retrives and returns host ip address."""
    return _retry_check_output(['hostname', '-I']).decode().split()[0]
