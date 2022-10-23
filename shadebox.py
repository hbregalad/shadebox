#!/usr/bin/env python3
###############################################################################

import os, sys, threading

from math import ceil
from flask import Flask, Response

from lib import *
#from pprint import pprint
#import time
#TODO:does hup kill this? can we make it not kill it?

app = Flask(__name__)
###############################################################################
#some constants we don't need anywhere else:

DEFAULT_REFRESH = 300 #in seconds
events = Event(0, 'dummy event', lambda:print("Event list created"))
motors = Driver()

###############################################################################

def render_main_page(message='Ready.', refresh=DEFAULT_REFRESH, reload='/'):
    """Code for main render."""
    doc = html()
    head = doc.head
    head.title.append("Shadebox: %s" % message)
    #head.meta(name="viewport", content="width=device-width, initial-scale=1")

    #print((reload, reload))
    if events :#if there are events other than the most recent one added, set refresh based on the soonest
        refresh = min(refresh, events.next().interval_remaining())

    head.meta(**{'http-equiv': 'refresh',
                 'content':    '%i;url=%s' % (ceil(refresh + .1), reload)
            })

    #use prerendered instead.
    #head.link(rel='stylesheet', type='text/css', href='/shadebox.css')
    #ead.meta(name="Keywords", content='shade,control,automation')
    head.append(STYLE)
    head.append(KEYWORDS)
    body = doc.body
    body_table = body.table
    body_table.tr.th(colspan='8').append(message)
    #table = body.table()
    for motor in motors:
        row = body_table.tr
        #row.td(**{'class':'odd' if motor % 2 else 'even'}).append('Motor{}: '.format(motor))

        row.td.append(motor[MOTOR_NAME]+':')
        for direction in DIRECTIONS[UP:DOWN+1]:
            #a= row.td(**{'class':'odd' if motor % 2 else 'even'}).a(href='/start/{}/{}'.format(motor, direction) )
            anchor = row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor[INDEX], direction[INDEX]) )
            anchor.append('%s' % direction[DIRECTION_CAPTION])
            if direction[INDEX] == motors.state[motor[INDEX]]:
                anchor.args['class']='mode'
            #row.append()

    lt = time.strftime(TIME_FORMAT_STRING, time.localtime()).replace(' 0',' ')
    body.p(align='center').append("Server local time is:%s" % lt)

    time_table = body.table
    time_table.tr.th(colspan='2').append("Scheduled events:")
    time_table_header = time_table.tr
    time_table_header.th.append("when")
    time_table_header.th.append("what")
    for event in events:
        row = time_table.tr
        row.td.append(event.format_interval())
        row.td.append(event.description())
    
    if admin_commands:
        ac = body.p(align='right')
        ac.append('admin commands:')
        for command in admin_commands:
            ac.a(href='/admin_command/%s' % command, indent='').append(command)
            ac.append(' :: ')
        #row.td.append('All:')

    #a=row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor[INDEX]+1, direction) )

    d=str(doc)
    print("    Bytes rendered:",len(d))
    return d#str(doc)

###############################################################################
admin_commands = 'quit update restart shutdown'.split()

@app.route('/admin_command/<command>')
def admin_command(command):
    doc = html()
    doc.title.append('result:')
    docb = doc.body
    doc_results = doc.p
    doc.p(align='right').a(href='/').append('return to Home')

    def die():
        log('trying to restart')
        server_thread.clear()

    def format_CompleteProcess(a):
        code, out = subprocess.getstatusoutput(a)
        s = "\n$ %s\noutput:\n%s\nReturn code: %s\n\n" % (
            a, out, code)
        log(s)
        return s, code

    if command=='restart':
        s, code = format_CompleteProcess('shutdown -r +5')
        doc_results.append(s.replace('\n','<br>'))
        return str(doc)
                        
    if command=='shutdown':
        s, code = format_CompleteProcess('shutdown -p +5')
        doc_results.append(s.replace('\n','<br>'))
        return str(doc)
    if command=='update':
        s, code = format_CompleteProcess('git pull')
        if not code:
            s2, code = format_CompleteProcess('%s setup.py' % sys.executable)
            s += s2
            if not code:
                s2, code = format_CompleteProcess('systemctl restart shadebox.service')
                s += s2
                if not code:
                    s+='Restarting shadebox server...'
                    Event(1,'Restarting shadebox server...', die)
        doc_results.append(s.replace('\n','<br>'))
        return str(doc)
    if command=='quit':
        Event(1, 'Exiting shadebox server...', die)
        return render_main_page("Quitting soon ...")

###############################################################################
# it's better to always an answer to both paths, even if we only build paths to
# one at a time. With the error pages redirecting to index, we don't want to fill
# up a browser cache with redirects that may someday come back
@app.route('/%s/<int:motor_index>/<int:direction_index>' % OTHER_START_PATH)
@app.route('/%s/<int:motor_index>/<int:direction_index>' % MOTOR_START_PATH)
def motor_start(motor_index, direction_index):
    """Here's the glue between Flask and relay_interface"""
    print("%r, %r" % (motor_index, direction_index))
    try:
        motor = motors[motor_index]
        print(motor)
    except IndexError:
        return render_main_page("No such Motor{}".format(motor))

    try:
        direction = DIRECTIONS[direction_index]
        print(direction)
    except IndexError:
        return render_main_page("No such direction{}".format(direction))

    motors.set(motor, direction)

    return render_main_page(
        '{} set to {}'.format(motor[MOTOR_NAME], direction[DIRECTION_NAME]),
        direction[TIMEOUT])

    

#def motor_set_state(motor, pins, direction, direction_data):
#    """ Outputs the new motor direction to GPIO,
#        Saves state to motor_state[],
#        starts a timer until reseting to STOP state."""
#    if pins:
#        GPIO.output(pins, direction_data[:2])
#        motor_state[motor] = direction
#    else:
#        for inner_motor, pins in enumerate(MOTOR_PINS):
#            if pins:
#                GPIO.output(pins, direction_data[:2])
#            motor_state[inner_motor] = direction
#
#    if direction_data[2]:
#        t = Timer(direction_data[2],
#           lambda: motor_set_state(motor, pins, STOP, DIRECTIONS[STOP])#after duration, set to stop
#           )
#       t.start()

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
    r = Response(ROBOT, mimetype  = 'text/plain')
    Response.expires
    return 

@app.route('/favicon.ico')
def favicon():
    """I chose a darkmode raspberrypi icon. There are others out there, suit yourself."""
    return Response(open('./static/favicon.png','rb').read(), mimetype = 'image/png')

def build_error_pages(PORT):
    """Prerendered error pages, and save."""
    address = 'http://%s:%i/' % (get_host_ip(), PORT)
    print ("build_errors() rendering with redirect location: %s" % address)
    if DEBUG:
        error_redirect = {400: 400, 403: 403, 404: 404, 410: 410, 500: 500}
    else:
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
        print (arg)
        try:
            err = int(str(arg)[:3])
            ep, new_err_num, loc = error_page[err]
        except ValueError:
            ep = render_main_page(str(arg), DEFAULT_REFRESH, address)
            new_err_num = 500
            loc = {'Location': address}
        if DEBUG:
            ep = ep + str(arg)
        return ep, new_err_num, loc
    for err in error_redirect:
        app.errorhandler(err)(error)
#build_error_pages()

###############################################################################

if __name__ == '__main__':
    
    def finish_test():
        """Call everything once, before we enter wait state, to fail early."""
        for f in (index, css, oh_no_robot, favicon):
            f()

        if True:#GPIO_DEBUG:
            #only test this if we're NOT talking to real hardware,
            #only spaming the debug handler...
            for motor, pins, name in motors:
                if not pins: continue
                motors.set(motor, motor)
        morning(True)
        evening(True)

    #TODO make these into json and editable
    def morning(startup=False):
        "What to do in the morning"
        #re/schedule self
        EventAt(6,0,0, "morning routine", morning, daemon=True)
        if not startup:#if alarm is really going off, do:
            print("morning alarm activated")
            motor_start(0, UP)
            motors.set(1, EXTENDED_TEST)
            #EventAt(7,0,0, "light off", lambda:motors.set(1, STOP))

    def evening(startup=False):
        "What to do in the evening"
        #re/schedule self
        EventAt(17,0,0, "evening routine", evening, daemon=True)
        if not startup:#if alarm is really going off, do:
            print("starting evening routine")
            motor_start(0, DOWN)


    def relocate():
        if os.getcwd() != os.path.abspath(__file__):
            newcwd = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-1])
            log('cd %s => %s' % (os.getcwd(), newcwd))
            os.chdir(newcwd)
        log("running with pid=%s in cwd=%s" % ( os.getpid(), os.getcwd() ), file=sys.stderr)
            
    with motors:
        relocate()
        finish_test()
        
        successes={}
        failures={}
        server_thread = []

        def startup(port):
            build_error_pages(port)
            try:
                successes[port]=True
                app.run(host = '0.0.0.0', port=port)
            except PermissionError:
                log('PermissionError: Port {} not allowed, trying alternate port'.format(port))
                del successes[port]
            finally:
                server_thread.clear()
            #except OSError:
            #    log('PermissionError: Port {} not allowed, trying alternate port'.format(port))

        for port in (80, 5000):#try each port in turn, but stop after one success
            thread = threading.Thread(target=startup, args=[port]
                                      , daemon=True
                                      )
            server_thread.append(thread)
            
            thread.start()
            #event = Event(.01, "start server", startup, [port])
            #event.timer.setDaemon()
            time.sleep(1)
            if len(successes):
                break
        
        try:
            while server_thread:
                time.sleep(1)
        finally:
            print('exiting something')
            events.cancel(True)
##            exit()
