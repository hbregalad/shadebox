from flask import Flask, Response, url_for
from threading import Timer
from lib import *
from math import ceil
from pprint import pprint

app = Flask(__name__)



@app.route('/')
def index():
    return main('Welcome to shadebox.')


def main(message='Ready.', refresh=DEFAULT_REFRESH, reload='/'):
    doc = html()
    head = doc.head
    head.title.append("Shadebox: %s" % message)
    #head.meta(name="viewport", content="width=device-width, initial-scale=1")

    #print((reload, reload))
    head.meta(**{'http-equiv': 'refresh',
                 'content':    '%i;url=%s' % (ceil(refresh + .1), reload)
            })

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
    print("    Bytes rendered:",len(d))
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


@app.route('/shadebox.css')
def css():
    """If we serve this seperately, a lot of browsers will cache it, saving bandwidth."""
    return Response(CSS, mimetype = 'text/css')

@app.route('/robots.txt')
def oh_no_robot():
    """Tell them not to browse the motor control interface."""
    return Response(ROBOT, mimetype  = 'text/plain')

@app.route('/favicon.ico')
def favicon():
    """I chose a darkmode raspberrypi icon. There are others out there, suit yourself."""
    return Response(open('static/favicon.png','rb').read() , mimetype = 'image/png')

def build_error_pages():
    address = 'http://%s:%i/' % (get_host_ip(), DEFAULT_PORT)
    print ("build_errors() rendering with redirect location: %s" % address)
    error_redirect = {400: 301, 403: 301, 404: 301, 410: 301, 500: 500}
    pprint(error_redirect)
    error_page = {
        error: (
            main("Error: %i Response: Redirect" % error,10,address),
            error_redirect[error],
            {'Location': address}
            )
        
        for error in error_redirect.keys()
    }
    def error(arg='400'):
        err = int(str(arg)[:3])
        return error_page[err]
    for err in error_redirect.keys():
        app.errorhandler(err)(error)

build_error_pages()


if __name__ == '__main__':
    

    with gpio_open([],all_motor_pins) as GPIO:
        app.run(host = '0.0.0.0', port=5000)
