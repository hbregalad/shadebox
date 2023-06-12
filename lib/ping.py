import subprocess, time


class Ping:
    def _load_default_gateway(self):
        code, out = subprocess.getstatusoutput('ip route')

        if code:return None
        out = out.replace('\n',' ').split()

        for i,v in enumerate(out):
            if v=='default':
                return out[i+2]

        return None
    def __init__(self, timeout_secs=300, count=4, sleep_func = time.sleep, time_func=time.time):
        self._sleep = sleep_func
        self._time = time_func
        self._timeout_secs = timeout_secs
        self._count = count

        self.default_gateway = self._load_default_gateway()

    def _get_metrics(self):
        """measures the ping time to default gateway
        saves results to ._last_measurement
        returns a dict whose keys are 'rtt min/avg/max/mdev' or whatever your ping sumary line looks like"""
        while not self.default_gateway:
            self._sleep(1)
            self.default_gateway = self._load_default_gateway()

        t = self._time()
##        print('{', end='')
        code, out = subprocess.getstatusoutput('ping %s -c %d' % (self.default_gateway, self._count))
##        print('}', end='')

        m, when = self._last_measure = dict(zip(*map(lambda s:s.strip().split('/'), out.strip().split('\n')[-1].split('=')))), t

        return m
    def get_metrics(self):
        """retrives the last measurement taken unless it's too old.
        returns a dict whose keys are 'rtt min/avg/max/mdev' or whatever your ping sumary line looks like"""
        m, when = getattr(self, '_last_measure', (None, 0))
        if when + self._timeout_secs > self._time():
            return m
        else:
            return self._get_metrics()

    def get_metric(self, key='avg'):
        return self.get_metrics()[key]

    def subscribe(self, key='avg'):
        while True:
            yield self.get_metric(key)
            self._sleep(self._timeout_secs - (self._time() - self._last_measure[1]))

if __name__=='__main__':
    p = Ping(5)
    for s in p.subscribe():
        print(s)
