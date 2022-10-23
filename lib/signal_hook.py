"signal_hook.py"
import signal

QUITING=False
def term(signum, frame):
    """translate SIGTERM into KeyboardInterupt so that app behaves similarly
    in userspace as in server space."""
    global QUITING
    QUITING=True
    raise KeyboardInterrupt("received signal %s" % signum)

signal.signal(signal.SIGTERM, term)

def quitting_sleep(seconds):
    assert not QUITING
    return time.sleep(seconds)
