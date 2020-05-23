#gpio_state.py
from contextlib import contextmanager
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO missing, logging all GPIO calls to stdout.")
    class GPIO:
        """class provided for debug purposes."""
        def __getattr__(self,name):
            def log(*args, **kargs):
                print("GPIO.%s(*%r,**%r)" % (name, args, kargs))
            return log

@contextmanager
def gpio_open(inpinlist, outpinlist):
    GPIO.setmode(GPIO.BOARD)
    #GPIO.setmode(GPIO.BCM)
    for pin in inpinlist:
        GPIO.setup(pin, GPIO.IN)

    for pin in outpinlist:
        GPIO.setup(pin, GPIO.IN)

    yield GPIO

    GPIO.cleanup()
