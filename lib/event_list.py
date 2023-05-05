"event_list.py"

from threading import Timer, current_thread, main_thread 		#the behavior we are wrapping
from math import ceil
from sys import stderr
from traceback import print_exc

import time

WARN = lambda *a,**k: print(*a, file=stderr, **k)

DATE_FORMAT_STRING = "%a %b %d, %H:%M"#' %H:%M:%S '
TIME_FORMAT_STRING = 'at %H:%M '#' %H:%M:%S '
MINUTES_FORMAT_STRING = 'in %H:%M:%S '
class Event:
    """Replacement for threading.Timer, but queryable."""
    EventList = {}#intentionally shared by all instances
    SawKeyboardInterrupt = []#used for inter-thread communication
    def _check_keyboard(self):
        "reraise keyboard interupt in main thread"
        if self.SawKeyboardInterrupt and current_thread() == main_thread():
            Ex = self.SawKeyboardInterrupt.pop()#receive Exception from other thread
            raise Ex #put back in circulation

    def trigger(self):
        "take care of some house keeping, then call the user event code"
        try:
            try:
                self.EventList.pop(self.id)
            except KeyError:
                WARN(self.id, "canceled, skipping")
                return
            action, args, kwargs = self.action

            try:
                action(*args, **kwargs)
            except RuntimeError:
                raise
            except Exception:
                WARN(self)
                WARN("%r(*%r, **%r)"%(action, args, kwargs))
                print_exc()
        except (KeyboardInterrupt, RuntimeError, SystemExit) as E:
            if current_thread() != main_thread():
                self.SawKeyboardInterrupt.append(E)
            else:
                raise

    def __init__(self, interval, description, action, action_args=None, action_kwargs=None, exclusive_description=True,
                 cancel_activates=False, daemon=True):
        """Drop in replacement for threading.Timer, but queryable
        if exclusive_description is True, will replace all previous events with the the same description
        otherwise will cancel only events with same expiration and description
        if cancel_activates is true, .cancel() will cause the event to activate immediatly.
        """
        self._check_keyboard()

        self.id = (time.time() + interval , description)
        action_args = action_args if action_args is not None else []
        action_kwargs = action_kwargs if action_kwargs is not None else {}

        if exclusive_description:
            for event in self:
                if event.description()==description:
                    event.cancel()
        else:
            for event in self:
                if event.id == self.id:
                    event.cancel()

        self.cancel_activates = cancel_activates
        #print(self.cancel_activates)
        self.action = action, action_args, action_kwargs

        self.EventList[self.id] = self

        if interval<=0:
            self.trigger()
            self._check_keyboard()
        else:
            timer = self.timer = Timer(interval, self.trigger)
            if daemon is not None:#Timer constructor doesn't provide a way to set this.
                timer.setDaemon(daemon)
            timer.start()

    def cancel(self, All=False):#, DontCheck=False):
        """prevent Event action from running
        set All to .cancel() all registerd soonest first
        set DontCheck to skip reraising KeyboardInterupt() if it happened inside an event.
        """

        work = list(self.EventList.values()) if All else [self]

        for event in work:
            #if not DontCheck:
            print('Canceling:', event.id[1])
            event.timer.cancel()#make sure that other thread does not run
            if event.cancel_activates:
                event.trigger()#run in this thread, immediatly
            else:
                try:
                    event.EventList.pop(event.id)
                except KeyError:
                    WARN("Event(%r) Warning: cancel() after Event already run or canceled. "%self.id)
                    return
                
        #if not DontCheck:
        self._check_keyboard()
    def cancel_by_description(self_or_cls, description):
        """Cancels all registered events matching [description]"""
        for event in list(self_or_cls.EventList.values()):
            if event.description() == description:
                event.cancel()
    def _check_expired(self):
        "Find all expired events and drop them from the .EventList"

        expire_time = time.time()-6*60*60 #allow one second I mean 6 minutes of scheduling flexibility before complaining.
        #I have had a timer execute 5 minutes and 2 seconds late. After more examples I will try to decide how to adjust our strategy.
        
        expired = [k for k in self.EventList
                   if k[0]<expire_time]

        if expired:
            WARN("Warning: expired events:%r" % expired)
            for k in expired:
                try:
                    #self.EventList.pop(k)
                    self.EventList[k].cancel()
                except KeyError:
                    pass
        self._check_keyboard()
    def __iter__(self):
        self._check_expired()
        return iter([e
                     for k, e in sorted(self.EventList.items())
                     ])
    def __len__(self):
        self._check_keyboard()
        return len(self.EventList)

    def when(self):
        "return the expire time for event"
        self._check_keyboard()
        return self.id[0]
    def interval_remaining(self):
        "return seconds remaining before event"
        self._check_keyboard()
        if self.id not in self.EventList: return 0 #canceled, don't wait.
        return max(0, self.id[0] - time.time())
    def format_interval(self):
        """formats the event time either as seconds remaining (if < 1 minute),
        or minutes & seconds remaining (if < 1 hour),
        or as the hours & minutes for the time of day it should go off (if > 1 hour)"""
        self._check_keyboard()
        ir = self.interval_remaining()
        if ir > 60*60:
            return time.strftime(TIME_FORMAT_STRING,
                time.localtime(self.when()))#.replace(' 00:',' ').replace(' 0',' ')
        elif ir > 60:
            return time.strftime(MINUTES_FORMAT_STRING,
                time.gmtime(ir)).replace(' 00:',' ').replace(' 0',' ')
        else:
            return str(ceil(ir)) + " secs"
    def description(self):
        "retrives the description field"
        self._check_keyboard()
        return self.id[1]

    def __repr__(self):
        return "Event(%r, %s)" % (self.interval_remaining(), self.id[1])
    def __str__(self):
        return "in: %r seconds do: %s" %(self.interval_remaining(),self.id[1])

    def next(self):
        "retrives the nearest remaining event."
        self._check_expired()
        if self.EventList:
            return self.EventList[min(self.EventList.keys())]
        #else:
        return self
    def last(self):
        "retrives the farthest remaining event."
        self._check_expired()
        return self.EventList[max(self.EventList.keys())]

    def join(self, Any=False, All=False, check_interval=.3):
        """sleep()s until this event is scheduled to have run.
        if Any is set, instead executes self.next().join()
        if All is set, instead executes self.last().join()"""

        
        if All:
            event = self.last()#.join()
        elif Any:
            event = self.next()#.join()
        else:
            event = self
            
        while check_interval < event.interval_remaining(): #self._check_keyboard() is happening inside
            time.sleep(check_interval)
        return time.sleep(max(0, event.interval_remaining()+.02))#no negative intervals
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return self.cancel(True)
DAY = 24*60*60
def mktime(hours=0, minutes=0, seconds=0):
    "returns time in seconds for when the given local time happens"
    print(hours, minutes, seconds)
    tl = list(time.localtime())
    tl[3:6] = hours, minutes, seconds
    return time.mktime(tuple(tl))
def midnight():
    "returns time in seconds for when the previous midnight"
    return mktime()

def EventAt(hours=0, minutes=0, seconds=0, description="Alarm",
            action=lambda:None, args=None, kwargs=None,
            exclusive_description=True, cancel_activates=False, daemon=True):
    """schedules an Event via hours, minutes, and seconds, instead of seconds into the future"""
    t = mktime(hours, minutes, seconds)
    if t<time.time(): t+=DAY
    return Event(t - time.time(), description, action, args, kwargs, exclusive_description, cancel_activates, daemon)

if __name__=='__main__':
    def die():
        print("ceaser we solute you")
        raise KeyboardInterrupt(die)
    def main():
        "test"
        
        for interval in range(5):
            event = Event(interval, "say %s" % interval, (lambda i:lambda:print(i))(interval))

        while event:
            print(list(event))
            event.join(Any=True)

        tomorrow = Event(DAY, "This time Tomorrow", print)
        _sunrise = EventAt(6)
        _sunset = EventAt(5+12, description="down")
        with tomorrow:
            for event in tomorrow:
                print(event)
                print(event.format_interval())
                event.cancel()

            #try:
            event = Event(0.01, 'die', die)
            print('got here')
            time.sleep(.1)
            print('got here')
            for event in event:
                print('got into loop')
                print('got out of loop')
##            finally:
##                event.cancel(True, True)
    main()
