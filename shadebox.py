#!/usr/bin/env python3
###############################################################################

import os, sys, threading

from math import ceil
from flask import Flask, Response, request

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
HORIZONTAL_GRID = False
VERTICLE_GRID = True

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

    def anchor(html_row, href, caption, highlighted=False, replace_v=False):
        anchor = html_row.td.a(href=href)
        if replace_v:
            caption = caption.replace('&lt;','^').replace('&gt;','v').replace('v|','v').replace('|^','^')
        anchor.append('%s' % caption)
        if highlighted: anchor.args['class']='mode'
    def mk_grid_item(html_row, motor, direction=None, replace_v=False):
        if direction is None:
            html_row.td.append(motor[MOTOR_NAME]+':')
        else:
            anchor(html_row,
                   '/{}/{}/{}'.format(MOTOR_START_PATH, motor[INDEX], direction[INDEX]),
                   direction[DIRECTION_CAPTION],
                   direction[INDEX] == motors.state[motor[INDEX]],
                   replace_v
                   )

    if HORIZONTAL_GRID:
        body_table = body.table
        body_table.tr.th(colspan='8').append(message)
        #table = body.table()
        for motor in motors:
            row = body_table.tr
            #row.td(**{'class':'odd' if motor % 2 else 'even'}).append('Motor{}: '.format(motor))
            mk_grid_item(row, motor)
            #row.td.append(motor[MOTOR_NAME]+':')
            for direction in DIRECTIONS[UP:DOWN+1]:
                mk_grid_item(row, motor, direction)
##                #a= row.td(**{'class':'odd' if motor % 2 else 'even'}).a(href='/start/{}/{}'.format(motor, direction) )
##                anchor = row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor[INDEX], direction[INDEX]))
##                anchor.append('%s' % direction[DIRECTION_CAPTION])
##                if direction[INDEX] == motors.state[motor[INDEX]]:
##                    anchor.args['class']='mode'
                #row.append()

    if VERTICLE_GRID:
        body_table = body.table
        body_table.tr.th(colspan='5').append(message)

        #print(DIRECTIONS[UP:DOWN+1])
        for direction in (None,) + DIRECTIONS[UP:DOWN+1]:
            row = body_table.tr

            for motor in motors:
                mk_grid_item(row, motor, direction, True)


    lt = time.strftime(TIME_FORMAT_STRING, time.localtime()).replace(' 0',' ')
    ut = time.strftime(DATE_FORMAT_STRING, time.localtime(LAST_UPDATE)).replace(' 0',' ')
    body.p(align='center').append("Server local time is: %s<br />Last update time was: %s" % (lt, ut))

    #TODO: I'd like a memory usage stat here or down by admin commands.
    time_table = body.table
    time_table.tr.th(colspan='3').append("Scheduled events:")
    time_table_header = time_table.tr
    time_table_header.th.append("when")
    time_table_header.th(colspan='2').append("what")
    for event in events:
        row = time_table.tr
        row.td.append(event.format_interval())
        row.td.append(event.description())

        row_td=row.td(align='right')
        if not event.cancel_activates:
            row_td.a(title='Cancel', href='/event/cancel/%s'%event.description().replace(' ','_')
                ).append('X')
            row_td.append(' : ')
        row_td.a(title='Trigger!', href='/event/trigger/%s'%event.description().replace(' ','_')
            ).append('!')

    if ADMIN_COMMANDS:
        ac = body.p(align='right')
        ac.append('admin commands:')
        for command in ADMIN_COMMANDS:
            ac.a(href='/admin_command/%s' % command, indent='').append(command)
            ac.append(' :: ')
        #row.td.append('All:')

    #a=row.td.a(href='/{}/{}/{}'.format(MOTOR_START_PATH, motor[INDEX]+1, direction) )

    d=str(doc)
    print("    Bytes rendered:",len(d))
    return d#str(doc)
###############################################################################
ADMIN_COMMANDS = 'status ping quit update restart shutdown'.split()

def format_CompleteProcess(shell_command, log_output=True):
    """Runs shell_command in a new process, and formats the results.
    set log_output to log to terminal also"""
    code, out = subprocess.getstatusoutput(shell_command)
    s = "\n$ %s\noutput:\n%s\nReturn code: %s\n\n" % (
        shell_command, out, code)

    if log_output: log(s)

    return s.replace('\n','<br>'), code

@app.route('/admin_command/<command>')
def admin_command(command):
    doc = html()
    doc.title.append('result:')
    docb = doc.body
    doc_results = doc.p
    doc.p(align='right').a(href='/').append('return to Home')
    if not motors.boards:# and command in 'update restart shutdown'.split():
        DEBUG_PREFIX = '#IN DEBUG MODE: ' #block commands from being interpreted, but continue
    else:
        DEBUG_PREFIX = ''

    def die():
        log('trying to restart')
        #server_thread.clear()
        #raise RuntimeError('Not running with the Werkzeug Server')
        raise KeyboardInterrupt()
        #exit()
##        die2()
##    def die2(): #this method is no longer part of werkzeug
##        func = request.environ.get('werkzeug.server.shutdown')
##        if func is None:
##            raise RuntimeError('Not running with the Werkzeug Server')
##        func()

    if command=='restart':
        s, code = format_CompleteProcess(DEBUG_PREFIX + 'shutdown -r +1')
        doc_results.append(s)
        return str(doc)

    if command=='shutdown':
        s, code = format_CompleteProcess(DEBUG_PREFIX + 'shutdown -P +1')
        doc_results.append(s)
        return str(doc)
    if command=='update':
        s, code = format_CompleteProcess(DEBUG_PREFIX + 'git pull')
        if not code:
            s2, code = format_CompleteProcess(DEBUG_PREFIX + 'sudo %s setup.py' % sys.executable)
            s += s2
            if not code:
                #s2, code = format_CompleteProcess('systemctl restart shadebox.service')
                #s += s2
                #if not code:
                    s+='Restarting shadebox server...'
                    Event(1,'Restarting shadebox server...', die)

        doc_results.append(s)
        return str(doc)
    if command=='quit':
        Event(1, 'Exiting shadebox server...', die)
        raise KeyboardInterrupt()
        return render_main_page("Quitting soon ...")
    if command=='status':
        s, code = format_CompleteProcess('systemctl status shadebox.service', False)
        doc_results.append(s)
        s, code = format_CompleteProcess('journalctl -u shadebox.service -b --no-pager', False)
        doc_results.append(s)
##        s, code = format_CompleteProcess('cat shadebox.log', False)
##        doc_results.append(s)
        return str(doc)
    if command=='ping':
        s, code = format_CompleteProcess('ifconfig')
        doc_results.append(s)

        s, code = format_CompleteProcess('ip route | grep default')
        doc_results.append(s)
        addrs = []
        try:
            addr = s.split()[2]
        except:
            return str(doc)

        for addr in addrs:
            s, code = format_CompleteProcess('ping %s -c 4' % addr)
        doc_results.append(s)
        return str(doc)

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

###############################################################################
@app.route('/event/<command>/<description>/')
def event_mod(command, description):
    for event in events:
        if event.description().replace(' ','_') == description:
            if command == 'cancel':
                event.cancel()
            elif command == 'trigger':
                event.trigger()
            else:
                return render_main_page('unknown command:' %  command)
            return render_main_page('event %s %sed' % (description, command)
                                    )
    else:
        return render_main_page('event not found: %s' % description)


def set_expiration(response, days=14):
    response.expires = time.gmtime(time.time() + days*DAY)
    return response

##def in_one_week():
##    t = time.time() + DAY * 7
##    #return time.strftime(' %a, %d %b %Y %H:%M:%S GMT', time.gmtime(t))
##    return time.gmtime(t)

@app.route('/')
def index():
    """Do you feel at home?"""
    return render_main_page('Welcome to shadebox.')

@app.route('/shadebox.css')
def css():
    """If we serve this seperately, a lot of browsers will cache it, saving bandwidth."""
    return set_expiration(Response(CSS, mimetype = 'text/css'))

@app.route('/robots.txt')
def oh_no_robot():
    """Tell them not to browse the motor control interface."""
    return set_expiration(Response(ROBOT, mimetype  = 'text/plain'))

@app.route('/favicon.ico')
def favicon():
    """I chose a darkmode raspberrypi icon. There are others out there, suit yourself."""
    with open('./static/favicon.png','rb') as f:
        data = f.read()

    return set_expiration(Response(data, mimetype = 'image/png'))

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

###############################################################################

if __name__ == '__main__':

    def finish_test():
        """Call everything once, before we enter wait state, to fail early."""
        for f in (index, css, oh_no_robot, favicon):
            f()

        if True:#not motors.boards:
            #only test this if we're NOT talking to real hardware,
            #only spaming the debug handler...
            for motor, pins, name in motors:
                if not pins: continue
                motors.set(motor, 2)#bump up
            time.sleep(1)
            for motor, pins, name in motors:
                motors.set(motor, STOP)
                #Actually no, this also safely tests Events and motor power,
                #the events should stop the motor after a tenth of a second (bump up)
                #and with this sleep()+ set(stop), it should also stop power even when events are not working.
                #and finally, the relay clicks serves to alert anyone physically present that the service is up and running.
        if not motors.boards:
            global ADMIN_COMMANDS
            ADMIN_COMMANDS = 'status quit'.split()#hide commnads that should not be run on debug machine.

        morning(True)
        reboot(True)
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

    def reboot(startup=False):
        """Until we figure out how the daemon is dying after about a week,
        reboot daily."""
        EventAt(8,0,0, "daily reboot", reboot, cancel_activates=True, daemon=True)
        if not startup:#if alarm is really going off, do:
            print("scheduled down time")
            admin_command('restart')

    def relocate():
        if os.getcwd() != os.path.abspath(__file__):
            newcwd = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-1])
            log('cd %s => %s' % (os.getcwd(), newcwd))
            os.chdir(newcwd)
        log("running with pid=%s in cwd=%s" % ( os.getpid(), os.getcwd() ), file=sys.stderr)

    with motors, events:
        relocate()
        finish_test()
        successes={}
        failures={}
        server_thread = []


        def startup(port):
            build_error_pages(port)
            t = time.time()
            try:
                successes[port] = True
                app.run(host = '0.0.0.0', port=port)

            except PermissionError:
                log('PermissionError: Port {} not allowed, trying alternate port'.format(port))
                log(time.time()-t, 'seconds')
                del successes[port]
            except Exception as E:
                log(''.join(traceback.format_exception(E)))
                log(time.time()-t, 'seconds')
                del successes[port]
            finally:
                server_thread.clear()

            #except OSError:
            #    log('PermissionError: Port {} not allowed, trying alternate port'.format(port))

        for port in (80, 5000):#try each port in turn, but stop after one success
            thread = threading.Thread(target=startup, args=[port], daemon=True)
            server_thread.append(thread)

            thread.start()
            #event = Event(.01, "start server", startup, [port])
            #event.timer.setDaemon()
            time.sleep(2)
            if len(successes):
                break

        #try:
##        try:
        while server_thread:
            events.join(All=True)
##        finally:
##            if server_thread:



        #finally:
        log('exiting')
        #    events.cancel(True,True)
##            exit()
    exit()
