from flask import Flask
from time import time
from lib import *

app = Flask(__name__)

@app.route('/')
def index():
    return main('Welcome to shadebox.')

def main(message='Ready.'):
    doc = html()
    doc.head()
    body = doc.body()
    body.h1(message)
    table = body.table()
    for motor in range(4):
        row = table.tr().td()
        row.append('Motor{}: '.format(motor))
        for direction, data in directions.items():
            a= row.a(href='/start/{}/{}'.format(direction, data[4]))
            if direction==motor_state[motor]:
                a.args['class']='motor_state'
            row.append('&nbsp;')

    return str(doc)

@app.route('/start/%i/%i')
def motor_start(motor, direction):
    try:
        motor_pins = motor_pins[motor]
    except KeyError:
        return main("No such Motor{}".format(motor))

    try:
        direction_data = directions[direction]
    except IndexError:
        return main("No such direction{}".format(direction))

    motor_set_state(motor_pins,direction_data,direction)

    return main('motor{} set to {}'.format(motor,direction_data[3]))

def motor_set_state(motor, motor_pins, direction, direction_data):
    GPIO.output(motor_pins, direction_data[:2])
    motor_state[motor] = direction
    if direction_data[2]:
        t = timer(
            time.time()+direction_data[2],
            lambda: motor_set_state(motor, motor_pins, 0, directions[0])#after duration, set to stop
            )
        t.start()

@app.route('/shadebox.css')
def css():
    return """
    a {
        color: blue;
    }
    a.motor_state {
        color: green;
        background-color: darkblue;
    }


if __name__ == '__main__':
    with gpio_open(all_motor_pins) as GPIO:
        app.run(address = '0.0.0.0', port=5000)
