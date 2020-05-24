#gpio_state.py
from contextlib import contextmanager
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO missing, logging all GPIO calls to stdout.")
    class _GPIO:
        """class provided for debug purposes."""
        #def __call__():
        #    pass
        #def __init__(self):
        #    print(self.__dict__.items())
        def __getattr__(self,name):
            print("GPIO attribute creation: %s" % name)
            class logger:
                def __call__(self, *args, **kargs):
                    print("GPIO.%s(%s, %s)" % (name, str(args)[1:-1], str(kargs)[1:-1]))
                def __repr__(self):
                    return 'GPIO.%s' % (name)
                def __str__(self):
                    return 'GPIO.%s' % (name)
            #def log(*args, **kargs):
            #    print("GPIO.%s(*%r,**%r)" % (name, args, kargs))
            new = logger()
            #super(self).__setattr__(name, new)
            self.__dict__[name]= new
            return new
    GPIO=_GPIO()

@contextmanager
def gpio_open(inpins=[], outpins=[]):
    """Setup and cleanup of GPIO driver state."""
    GPIO.setmode(GPIO.BOARD)
    #GPIO.setmode(GPIO.BCM)
    for pin in inpins:
        GPIO.setup(pin, GPIO.IN)

    for pin in outpins:
        GPIO.setup(pin, GPIO.OUT)

    yield GPIO

    GPIO.cleanup()


