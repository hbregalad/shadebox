#/usr/bin/env python3
###############################################################################

from flask import Flask, Response
from threading import Timer
from lib import *
from math import ceil
from pprint import pprint

app = Flask(__name__)

###############################################################################

def render_main_page(message='Ready.', refresh=DEFAULT_REFRESH, reload='/'):
    """Code for main render."""
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
    for motor, _pins in enumerate(MOTOR_PINS):
        row = body_table.tr
        #row.td(**{'class':'odd' if motor % 2 else 'even'}).append('Motor{}: '.format(motor))

        row.td.append(motor_name(motor)+':')
        for direction, data in enumerate(DIRECTIONS):
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

###############################################################################
# it's better to always an answer to both paths, even if we only build paths to
# one at a time. With the error pages redirecting to index, we don't want to fill
# up a browser cache with redirects that may someday come back
@app.route('/%s/<int:motor>/<int:direction>' % OTHER_START_PATH)
@app.route('/%s/<int:motor>/<int:direction>' % MOTOR_START_PATH)
def motor_start(motor, direction):
    """Here's the glue between Flask and GPIO"""
    try:
        pins = MOTOR_PINS[motor]
    except KeyError:
        return render_main_page("No such Motor{}".format(motor))

    try:
        direction_data = DIRECTIONS[direction]
    except IndexError:
        return render_main_page("No such direction{}".format(direction))

    motor_set_state(motor, pins, direction, direction_data)

    return render_main_page(
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
        for inner_motor, pins in enumerate(MOTOR_PINS):
            if pins:
                GPIO.output(pins, direction_data[:2])
            motor_state[inner_motor] = direction

    if direction_data[2]:
        t = Timer(direction_data[2],
            lambda: motor_set_state(motor, pins, STOP, DIRECTIONS[STOP])#after duration, set to stop
            )
        t.start()

###############################################################################

@app.route('/')
def index():
    """Do you feel at home?"""
    return render_main_page('Welcome to shadebox.')

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
    """Prerendered error pages, and save."""
    address = 'http://%s:%i/' % (get_host_ip(), DEFAULT_PORT)
    print ("build_errors() rendering with redirect location: %s" % address)
    error_redirect = {400: 301, 403: 301, 404: 301, 410: 301, 500: 500}
    error_page = {
        error: (
            render_main_page("Error: %i Response: Redirect" % error,10,address),
            error_redirect[error],
            {'Location': address}
            )

        for error,redirect in error_redirect.items()
    }
    def error(arg='400'):
        err = int(str(arg)[:3])
        return error_page[err]
    for err in error_redirect.keys():
        app.errorhandler(err)(error)
build_error_pages()

###############################################################################

if __name__ == '__main__':
    def finish_test():
        """Call everything once, before we enter wait state, to fail early."""
        for f in (index, css, oh_no_robot, favicon):
            f()
            
        if GPIO_DEBUG:
            #only test this if we're NOT talking to real hardware,
            #only spaming the debug handler...
            for motor,pins in enumerate(MOTOR_PINS):
                if not pins: continue
                
                motor_start(motor, motor)
        
    with gpio_open([],all_motor_pins) as GPIO:
        finish_test()
        app.run(host = '0.0.0.0', port=5000)
