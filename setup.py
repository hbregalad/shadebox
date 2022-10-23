"setup.py"
import os

MAIN = __file__.replace('setup.py', 'main.py')
LOG = __file__.replace('setup.py', 'shadebox.log')

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
WantedBy=multi-user.target""".format(MAIN, LOG)

SERVICE = __file__.replace('setup.py', 'shadebox.service')
with open(SERVICE, 'w') as f:
    f.write(SERVICE_DATA)

os.symlink(SERVICE, '/etc/systemd/system/shadebox.service')
