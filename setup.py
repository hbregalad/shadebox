#!sudo env python3 setup.py
"setup.py"
import os, sys, traceback
import subprocess
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

#working: ExecStart=/usr/bin/nohup {2} {0} | tee -a {1}
#not working ExecStart=sh -c '/usr/bin/nohup {2} {0} | tee -a {1}'

# > {1} 2>&1



def which(command):
    ret =  subprocess.check_output(['which', command]).decode().rstrip()
    print (command,'=',repr(ret))
    return ret

systemctl = which('systemctl')
chmod = which('chmod')
#sudo = which('sudo')#not needed either we're running as root or there's no point?

def make_service(file):
    main = file.replace('setup.py', 'shadebox.py')
    log = file.replace('setup.py', 'shadebox.log')
    service = file.replace('setup.py', 'shadebox.service')
    destination = '/etc/systemd/system/shadebox.service'

    with open(log, mode='w') as f:
        f.write('log created')
    
    print(main, log, service, sep='\n')
    
    data = SERVICE_DATA.format(main, log, sys.executable)

    with open(service, 'w') as f:
        f.write(data)
        
    try:
        subprocess.check_output([chmod, '664', destination])
    except Exception as E:
        print("Error setting log permissions.")

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


make_service(os.path.abspath(__file__))
