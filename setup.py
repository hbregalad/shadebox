"setup.py"
import os#, sys
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
ExecStart=/usr/bin/env python3 {0} &>> {1}

[Install]
WantedBy=multi-user.target
"""

def make_service(file):
    main = file.replace('setup.py', 'main.py')
    log = file.replace('setup.py', 'shadebox.log')
    service = file.replace('setup.py', 'shadebox.service')
    destination = '/etc/systemd/system/shadebox.service'

    with open(log, mode='w') as f:
        f.write('log created')
    
    print(main, log, service, sep='\n')
    
    data = SERVICE_DATA.format(main, log)

    with open(service, 'w') as f:
        f.write(data)

    try:
        os.remove(destination)
    except:
        pass
    os.symlink(service, destination)
    subprocess.check_output('systemctl','enable','shadebox')

make_service(os.path.abspath(__file__))
