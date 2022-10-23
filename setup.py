"setup.py"
import os#, sys
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
ExecStart=/usr/bin/python3 {0} >> {1}

[Install]
WantedBy=multi-user.target"""

def make_service(file):
    main = file.replace('setup.py', 'main.py')
    log = file.replace('setup.py', 'shadebox.log')
    service = file.replace('setup.py', 'shadebox.service')

    with open(log, mode='w') as f:
        f.write('log created')
    
    print(main, log, service, sep='\n')
    
    data = SERVICE_DATA.format(main, log)

    with open(service, 'w') as f:
        f.write(data)

    os.symlink(service, '/etc/systemd/system/shadebox.service')

make_service(os.path.abspath(__file__))
