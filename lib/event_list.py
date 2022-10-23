"event_list.py"

from threading import Timer 		#the behavior we are wrapping
from math import ceil
from sys import stderr
from traceback import print_exc

import time

WARN = lambda *a,**k: print(*a, file=stderr, **k)

TIME_FORMAT_STRING = 'at %H:%M '#' %H:%M:%S '
MINUTES_FORMAT_STRING = 'in %H:%M:%S '
class Event:
    """Replacement for threading.Timer, but queryable."""
    EventList = {}#intentionally shared by all instances
    def wrap_action(self, action, args, kwargs):
        "take care of some house keeping before running user event code"
        try:
            self.EventList.pop(self.id)
        except KeyError:
            WARN(self.id, "canceled, skipping")
            return

        try:
            action(*args, **kwargs)
        except:
            print(self)
            print("%r(*%r, **%r)"%(action, args, kwargs))
            print_exc()
            raise

    def __init__(self, interval, description, action, args=None, kwargs=None, exclusive_description=True):
        """Drop in replacement for threading.Timer, but queryable
        if exclusive_description is True, will cancel all previous events with the the same description
        otherwise will cancel only events with same expiration and description
        """

        self.id = (time.time() + interval , description)
        args = args if args is not None else []
        kwargs = kwargs if kwargs is not None else {}

        if exclusive_description:
            for event in self:
                if event.description()==description:
                    event.cancel()
        else:
            for event in self:
                if event.id == self.id:
                    event.cancel()

        self.EventList[self.id] = self
        if interval<=0:
            self.wrap_action(action, args, kwargs)
        else:
            self.timer = Timer(interval, lambda:self.wrap_action(action, args, kwargs))
            self.timer.start()

    def cancel(self):
        "prevent Event action from running"
        try:
            self.EventList.pop(self.id)
        except KeyError:
            WARN("Event(%r) Warning: cancel() after Event already run or canceled. "%self.id)
            return
        self.timer.cancel()#not sure if we really want to do this.

    def _check_expired(self):
        "Find all expired events and drop them from the .EventList"
        expire_time = time.time()-1#allow one second of scheduling flexibility before complaining.
        expired = [k for k in self.EventList
                   if k[0]<expire_time]

        if expired:
            WARN("Warning: expired events:%r" % expired)
            for k in expired:
                try:
                    self.EventList.pop(k)
                except KeyError:
                    pass

    def __iter__(self):
        self._check_expired()
        return iter([e
                     for k, e in sorted(self.EventList.items())
                     ])
    def __len__(self):
        return len(self.EventList)

    def when(self):
        "return the expire time for event"
        return self.id[0]
    def interval_remaining(self):
        "return seconds remaining before event"
        return max(0, self.id[0] - time.time())
    def format_interval(self):
        """formats the event time either as seconds remaining (if < 1 minute),
        or minutes & seconds remaining (if < 1 hour),
        or as the hours & minutes for the time of day it should go off (if > 1 hour)"""
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

    def join(self, Any=False, All=False):
        """sleep()s until this event is scheduled to have run.
        if Any is set, instead executes self.next().join()
        if All is set, instead executes self.last().join()"""
        if All:
            return self.last().join()
        elif Any:
            return self.next().join()
        else:
            return time.sleep(max(0, self.interval_remaining()+.02))

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

def EventAt(hours=0, minutes=0, seconds=0, description="Alarm", action=lambda:None, args=None, kwargs=None):
    """schedules an Event via hours, minutes, and seconds, instead of seconds into the future"""
    t = mktime(hours, minutes, seconds)
    if t<time.time(): t+=DAY
    return Event(t - time.time(), description, action, args, kwargs)

if __name__=='__main__':
    def main():
        "test"
        for interval in range(5):
            event = Event(interval, "say %s" % interval, (lambda i:lambda:print(i))(interval))

        while event:
            print(list(event))
            event.join(Any=True)

        tomorrow = Event(24*60*60, "This time Tomorrow", print)
        _sunrise = EventAt(6)
        _sunset = EventAt(5+12, description="down")
        for event in tomorrow:
            print(event)
            print(event.format_interval())
            event.cancel()


    main()
