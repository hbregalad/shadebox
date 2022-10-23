"setup.py"
import os, sys
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
ExecStart=/usr/bin/nohup {2} {0} > {1} 2>&1
Restart=on-failure
ExecStop=/bin/kill -INT $MAINPID

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
    
    data = SERVICE_DATA.format(main, log, sys.executable)

    with open(service, 'w') as f:
        f.write(data)

    try:
        os.remove(destination)
    except:
        pass
    try:
        os.symlink(service, destination)
        subprocess.check_output(['/bin/systemctl','enable','shadebox.service'])
        subprocess.check_output(['sudo', 'chmod', '664', destination])
    except:
        print("try sudo env python3 setup.py")
        raise


make_service(os.path.abspath(__file__))
