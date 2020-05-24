from flask import Flask, Response
from threading import Timer
from lib import *
from math import ceil

app = Flask(__name__)



@app.route('/')
def index():
    return main('Welcome to shadebox.')


def main(message='Ready.', reload=default_refresh):
    doc = html()
    head = doc.head
    head.title.append("Shadebox: %s" % message)
    #head.meta(name="viewport", content="width=device-width, initial-scale=1")

    head.meta(**{'http-equiv':'refresh', 'content':'%i;url=/' % ceil(reload+.1)})

    #use prerendered instead.
    #head.link(rel='stylesheet', type='text/css', href='/shadebox.css')
    #ead.meta(name="Keywords", content='shade,control,automation')
    head.append(STYLE)
    head.append(KEYWORDS)
    body_table = doc.body.table
    body_table.tr.th(colspan='8').append(message)
    #table = body.table()
    for motor, _pins in enumerate(motor_pins):
        row = body_table.tr
        #row.td(**{'class':'odd' if motor % 2 else 'even'}).append('Motor{}: '.format(motor))

        row.td.append(motor_name(motor)+':')
        for direction, data in enumerate(directions):
            #a= row.td(**{'class':'odd' if motor % 2 else 'even'}).a(href='/start/{}/{}'.format(motor, direction) )
            a = row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor, direction) )
            a.append('%s' % data[4])
            if direction==motor_state[motor]:
                a.args['class']='mode'
            #row.append()

    #row.td.append('All:')

    a=row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor+1, direction) )

    d=str(doc)
    print(len(d))
    return d#str(doc)

@app.route('/%s/<int:motor>/<int:direction>' % MOTOR_START_PATH)
def motor_start(motor, direction):
    try:
        pins = motor_pins[motor]
    except KeyError:
        return main("No such Motor{}".format(motor))

    try:
        direction_data = directions[direction]
    except IndexError:
        return main("No such direction{}".format(direction))

    motor_set_state(motor, pins, direction, direction_data)

    return main(
        '{} set to {}'.format(motor_name(motor), direction_data[3]),
        direction_data[2])

def motor_set_state(motor, pins, direction, direction_data):
    """ Outputs the new motor direction to GPIO,
        Saves state to motor_state[],
        starts a timer until reseting to STOP state."""
    if pins:
        GPIO.output(pins, direction_data[:2])
        motor_state[motor] = direction
    else:
        for inner_motor, pins in enumerate(motor_pins):
            if pins:
                GPIO.output(pins, direction_data[:2])
            motor_state[inner_motor] = direction

    if direction_data[2]:
        t = Timer(direction_data[2],
            lambda: motor_set_state(motor, pins, STOP, directions[STOP])#after duration, set to stop
            )
        t.start()

#@app.route('/favicon.ico')

@app.route('/shadebox.css')
def css():
    return Response(CSS, mimetype = 'text/css')

@app.route('/robots.txt')
def oh_no_robot():
    return ROBOT



if __name__ == '__main__':
    with gpio_open(all_motor_pins) as GPIO:
        app.run(host = '0.0.0.0', port=5000)
