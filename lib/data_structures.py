#data.py

directions={
    -3: (0,1,False,'Up','<<<'),# up forever
    -2: (0,1,5,'Up','<<'),    # up for 5 seconds
    -1: (0,1,.1,'Up','|<'),   # up for .1 seconds
    0: (0,0,False,'Stop','||'), #stop
    1: (1,0,.1,'Down','>|'),    # down for .1 seconds
    2: (1,0,5,'Down','>>'),     # down for .1 seconds
    3: (1,0,False,'Down','>>>'), # down for .1 seconds
}

motor_pins=(
    (0,1),
    (2,3),
    (4,4),
    (5,6),
)

all_motor_pins = []
for pins in motor_pins:
    all_motor_pins.extend(pins)
all_motor_pins = tuple(all_motor_pins)

#This is the only data volitile between threads. It's just ints in a list, it
#should be threadsafe.

motor_state=[0,0,0,0]
