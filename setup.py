#!sudo env python3 setup.py
"setup.py"
import os, sys, traceback
import subprocess
import time
#if __file__:

#print(__file__)
#print(sys.argv[0])
#f = os.path.abspath(__file__)
##print(f)
##f = os.path.abspath(sys.argv[0])
##print(f)

SERVICE_DATA = """[Unit]
Description=shadebox service
After=multi-user.target
Wants=systemd-timesyncd.service
After=systemd-timesyncd.service
ConditionPathExists={0}

[Service]
Type=idle
ExecStart=/usr/bin/nohup {2} {0}
ExecStop=/bin/kill --signal SIGINT $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""



# > {1} 2>&1
#ExecStart=/bin/sh -c '/usr/bin/nohup {2} {0} | tee -a {1}'


def which(command):
    "retrives the full path of command"
    ret =  subprocess.check_output(['which', command]).decode().rstrip()
    print (command, '=', repr(ret))
    return ret

systemctl = which('systemctl')
chmod = which('chmod')
crontab = which('crontab')

def modify_chrontab(newline, command):
    """replaces every non-commented line of chrontab
    which contains [command] with [newline]
    if no such lines were found, appends [newline]
    """
    assert b'\n' not in newline
    #thoughts, no point in replacing more than one, remove the rest?
    table = subprocess.check_output([crontab, '-l'])
    #print(repr(table))
    present = False
    
    new_table = []
    for line in table.split(b'\n'):
        if line.lstrip().startswith(b'#'):
            new_table.append(line)
        elif command in line:
            new_table.append(newline)
            present = True#don't add
        else:
            new_table.append(line)
    if not present:
        new_table.append(newline)
        new_table.append(b'')#adds a newline
    #print(new_table)
    table = b'\n'.join(new_table)
    
    with open('temp_cron','wb') as f:
        f.write(table)
        
    subprocess.check_call([crontab, 'temp_cron'])
    os.remove('temp_cron')
    
#sudo = which('sudo')#not needed either we're running as root or there's no point?

def make_service(file):
    main = file.replace('setup.py', 'shadebox.py')
    log = file.replace('setup.py', 'shadebox.log')
    service = file.replace('setup.py', 'shadebox.service')
    destination = '/etc/systemd/system/shadebox.service'

    checkwifi = file.replace('setup.py', 'checkwifi.sh')
    
##    with open(log, mode='w') as f:
##        f.write('log created')
    
    print(main, log, service, sep='\n')
    
    data = SERVICE_DATA.format(main, log, sys.executable)

    with open(service, 'w') as f:
        f.write(data)
        
##    try:
##        subprocess.check_output([chmod, '664', destination])
##    except Exception as E:
##        print("Error setting log permissions.")

    try:
        os.remove(destination)
    except Exception as E:
        print("Error removing destination:", E)
    
    try:
        os.link(service, destination)
        subprocess.check_output([chmod, '664', destination])
        subprocess.check_output([systemctl, 'enable', destination]) #, '--now'])
        #subprocess.Popen(
        
    except Exception as E:
        traceback.print_exc()
        print("try sudo env python3 setup.py")
        raise

    try:
        subprocess.check_output([chmod, '775', checkwifi])
        modify_chrontab(b'*/5 * * * * /usr/bin/sudo -H /usr/local/bin/checkwifi.sh >> /dev/null 2>&1',
                     b'checkwifi.sh')
    except Exception as E:
        print("Error setting up network auto-restart")
        traceback.print_exc()
        raise
    


if __name__=='__main__':
    make_service(os.path.abspath(__file__))

    version_file = __file__.replace('setup.py', os.sep.join(['lib','version.py']))
    with open(version_file, 'w') as f:
        print('LAST_UPDATE =', time.time(), '\n', file=f)
