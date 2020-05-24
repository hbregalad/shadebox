#data.py

directions=(
    (0, 1, 30,   'Up', '&lt;&lt;&lt;'), # up forever
    (0, 1,  5,   'Up',     '&lt;&lt;'), # up for 5 seconds
    (0, 1, .1,   'Up',        '|&lt;'), # up for .1 seconds
    (0, 0,  0, 'Stop',           '||'), #stop
    (1, 0, .1, 'Down',        '&gt;|'), # down for .1 seconds
    (1, 0,  5, 'Down',     '&gt;&gt;'), # down for .1 seconds
    (1, 0, 30, 'Down', '&gt;&gt;&gt;'), # down for .1 seconds
)
STOP = 3
motor_pins=(
    (0,1),
    (2,3),
    (4,4),
    (5,6),
    tuple()
)
def motor_name(index):
    try:
        pins = motor_pins[index]
    except IndexError:
        return '[Invalid Motor Index]'

    return 'Motor{}'.format(index) if pins else 'All'
all_motor_pins = []

for pins in motor_pins:
    all_motor_pins.extend(pins)
all_motor_pins = tuple(all_motor_pins)

#motor_pins.append(all_motor_pins)

default_refresh=300 #seconds





#This is the only data volitile between threads. It's just ints in a list, it
#should be threadsafe.
motor_state=[STOP,STOP,STOP,STOP,STOP]
