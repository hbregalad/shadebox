#querys.py
from pprint import pprint
import subprocess

def _retry_check_output(*args, **kargs):
    while True:
        try:
            return subprocess.check_output(*args, **kargs)
        except BlockingIOError: #swollow blocking errors and retry, but still fail on subprocess.TimeoutExpired errors
            time.sleep(.01)
            continue

def parse_ifconfig():
    """captures the output of ifconfig, and interprets it the best it can."""
    response = _retry_check_output('ifconfig').decode()

    last_interface = {}
    ret = {'pre':last_interface}
    for whole_line in response.splitlines():
        if not whole_line:
            continue

        i_line = iter(whole_line.split())
        if whole_line[0] != ' ':
            last_interface = {}
            ret[next(i_line)] = last_interface

        path = ''

        while i_line:
            try:
                item = next(i_line)
            except StopIteration:
                break
            if ':' in item:
                subpath, value = item.split(':')
                if value=='':
                    subpath, value = item, next(i_line)

                last_interface[path+subpath]=value
            else:
                if item == 'HWaddr':
                    path = path + item
                    value = next(i_line)
                    last_interface[item]=value
                elif item in ('UP','DOWN','BROADCAST','MULTICAST','LOOPBACK'):
                    last_interface[item]=True
                elif item[0]=='(':
                    while item[-1] != ')' and i_line:
                        try:
                            item += next(i_line)
                        except StopIteration:
                            break
                else:
                    path = item+' '

    assert len(ret['pre'])==0, "parse_ifconfig: local ifconfig seems to use a different format."
    del ret['pre']

    return ret

def get_host_ip():
    """Retrives and returns host ip address."""
    interfaces = parse_ifconfig()
    addresses =[]
    for interface, data in interfaces.items():
        for k,v in data.items():
            if ' addr' in k and ':' not in v:
                addresses.append(v)

    if len(addresses) > 1:
        for addr in addresses:
            if '127.' not in addr:
                return addr
    elif addresses:
        return addresses[0]
    else:
        raise RuntimeError("ifconfig response not understood or no ipv4 addresses")

