"relay_interface.py"
import subprocess
#from contextlib import contextmanager	#to automate some cleanup.
from itertools import count		#to help index some things
#from threading import Timer		#used for time outs
try:
    from event_list import Event
except ImportError:
    from .event_list import Event

DIRECTIONS=(
    #index, pin data, timeout, direction_name, link_caption
    (0, (0, 1), 30,   'Up', '&lt;&lt;&lt;'), # up 'forever' = 30 seconds
    (1, (0, 1),  5,   'Up',     '&lt;&lt;'), # up for 5 seconds
    (2, (0, 1), .1,   'Up',        '|&lt;'), # up for .1 seconds
    (3, (0, 0),  0, 'Stop',           '||'), #stop
    (4, (1, 0), .1, 'Down',        '&gt;|'), # down for .1 seconds
    (5, (1, 0),  5, 'Down',     '&gt;&gt;'), # down for 5 seconds
    (6, (1, 0), 30, 'Down', '&gt;&gt;&gt;'), # down 'forever' = 30 seconds
    (7, (1, 0), 60*60, 'Extended Test', '!!!'), # down 'forever' = 1 hour
)
UP = 0
STOP = 3
DOWN = 6
EXTENDED_TEST = 7

INDEX=0
PIN_DATA=1
TIMEOUT=2
DIRECTION_NAME=3
DIRECTION_CAPTION=4

##########################################################################
def _retry_check_output(*args, **kargs):
    """Same as subprocess.check_output, but tries not to take no for an answer."""
    retries = 5
    while retries:
        retries-=1
        try:
            return subprocess.check_output(*args, **kargs).decode()
        except BlockingIOError: #swollow blocking errors and retry, but still fail on subprocess.TimeoutExpired errors
            time.sleep(.01)
            continue


#this doesn't really belong here, but it's the only other thing that uses _retry_check_output() and i didn't feel like putting that in a seperate library file.
def get_host_ip():
    """Retrives and returns host ip address."""
    return _retry_check_output(['hostname', '-I']).split()[0]
##########################################################################

DEBUG = True
if DEBUG:
    log = print
else:
    log = lambda *args, **kargs: None

#INDEX=0
CHANNEL_DATA = 1
MOTOR_NAME = 2
##########################################################################
class Driver:
    def __init__(self):
        """Initialise driver"""
        #This retrives & parses a list of boards.

        try:
            boards = _retry_check_output(['8relay','-list']).splitlines()[1:]
        except FileNotFoundError:
            #self.boards = tuple()
            self.motors = ((0, ((0, 0), (0, 8)), "FakeMotor0:0"),
                           (1, ((1, 0), (1, 8)), "FakeMotor1:0"),
                           (2, ((True,True),(False,False)), "All"),
                           )
            self.state = [STOP] * (len(self.motors)+1)
            #self.set()#sets all to 0
            return

        self.boards = tuple( map( lambda a: a.split()[-1], boards) ) #I don't trust this to work on multiple boards, fix this if multiple boards needed or driver's -list format changes.
        log("8relay boards found: {}".format(self.boards) )
        index = count()
        #This builds the list of boards we'll be using.
        #The data structure is just a tuple of ( index,
        #                                        ((board_id,pin_down), (board_id,pin_up)),
        #                                        'motor{board}:{shade_number}',
        #                                        state,
        #                                    )
        self.motors = tuple( (
            (next(index),
            ((board, channel[0]), (board, channel[1])),
            'motor%s:%s' % (board, shade_no)
            )
            for board in self.boards
                for shade_no, channel in enumerate( (('1','2'),('3','4'),('5','6'),('7','8')) )
        ) ) + ( (next(index), tuple(), "All"), )


        self.state = [STOP] * (len(self.motors)+1)
        self.set()#sets all to 0
    def _set_channels(self, motor, direction):
        for channel, bit in zip(motor[CHANNEL_DATA], direction[PIN_DATA]):
            board_id, channel_id = channel
            try:
                out = _retry_check_output(['8relay', str(board_id), 'write', str(channel_id), str(bit)])
            except FileNotFoundError:
                pass

            #log(out)

            #log("Channel {} set to {}".format(channel, bit))
        self.state[motor[INDEX]] = direction[INDEX]
        log("{} set to {}".format(motor[MOTOR_NAME],direction[DIRECTION_NAME]))

    def set(self, motor=False, direction=STOP):
        """Sets the direction of a motor. Use False to send to all motors."""
        if isinstance(direction, int):
            try:
                direction = DIRECTIONS[direction]
            except (KeyError, IndexError) as E:
                raise ValueError(
                    "direction not recognised in dirver.set(motor:{},direction:{})".format(
                        motor, direction)
                    ) from E
        elif isinstance(direction, tuple):
            assert DIRECTIONS.index(direction) == direction[0], ValueError(
                "direction not recognised in dirver.set(motor:{},direction:{})".format(
                    motor, direction)
                )
        else:
            raise ValueError(
                "direction not recognised in dirver.set(motor:{},direction:{})".format(
                    motor,direction)
                )

        if motor is False:
            for motor in self.motors[:-1]:
                self.set(motor, direction)
            return

        if isinstance(motor, (int, str)):
            try:
                motor_data = self.motors[int(motor)]
            except (ValueError,IndexError) as E:
                raise ValueError(
                    "Motor not recognised in driver.set(motor:{}, direction:{})".format(
                        motor,direction)
                    ) from E
        elif isinstance(motor, tuple):
            motor_data, motor = motor, motor[0]
        else:
            raise ValueError(
                "Motor not recognised in driver.set(motor:{}, direction:{})".format(
                    motor,direction)
                )

        if motor_data[INDEX] == len(self.motors)-1:#all
            self.state[motor] = direction[INDEX]
            for motor in self.motors[:-1]:
                self._set_channels(motor, direction)
            if direction[TIMEOUT]:#set timeout as apropriate
                Event(direction[TIMEOUT],
                    "motor=%s stop" % motor_data[INDEX],
                    lambda: self.set(motor_data, DIRECTIONS[STOP])
                )
            else:
                Event.cancel_by_description(Event, "motor=%s stop" % motor_data[INDEX])
        else:
            self._set_channels(motor_data, direction)

            if direction[TIMEOUT]:#set timeout as apropriate
                Event(direction[TIMEOUT],
                    "motor=%s stop" % motor,
                    lambda: self._set_channels(motor_data, DIRECTIONS[STOP])
                )
            else:
                Event.cancel_by_description(Event, "motor=%s stop" % motor)
    def __iter__(self):
        yield from iter(self.motors)
        #yield self.all
    def __enter__(self):
        """Return list of motors"""
        return self
    def __exit__(self, *args):
        self.set()#sets all to stop
    def __getitem__(self, val):
        return self.motors[val]



#try:
#    import RPi.GPIO as GPIO
#    GPIO_DEBUG=False
#
#except ImportError:
#    print("RPi.GPIO missing, logging all GPIO calls to stdout.")
#    GPIO_DEBUG=True
#
#    class _GPIO:
#        """class provided for debug purposes."""
#        #def __call__():
#        #    pass
#        #def __init__(self):
#        #    print(self.__dict__.items())
#        def __getattr__(self,name):
#            print("GPIO attribute creation: %s" % name)
#            class logger:
#                def __call__(self, *args, **kargs):
#                    print("GPIO.%s(%s, %s)" % (name, str(args)[1:-1], str(kargs)[1:-1]))
#                def __repr__(self):
#                    return 'GPIO.%s' % (name)
#                def __str__(self):
#                    return 'GPIO.%s' % (name)
#            #def log(*args, **kargs):
#            #    print("GPIO.%s(*%r,**%r)" % (name, args, kargs))
#            new = logger()
#            #super(self).__setattr__(name, new)
#            self.__dict__[name]= new
#            return new
#    GPIO=_GPIO()
#
#@contextmanager
#def gpio_open(inpins=[], outpins=[]):
#    """Setup and cleanup of GPIO driver state."""
#    GPIO.setmode(GPIO.BOARD)
#    #GPIO.setmode(GPIO.BCM)
#    for pin in inpins:
#        GPIO.setup(pin, GPIO.IN)#
#
#    for pin in outpins:
#        GPIO.setup(pin, GPIO.OUT)
#
#    yield GPIO
#
#    GPIO.cleanup()
