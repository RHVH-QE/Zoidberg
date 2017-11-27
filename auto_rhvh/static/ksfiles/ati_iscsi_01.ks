### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###

### Security ###

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-pet105-01, which is a single path iSCSI machine, use the iSCSI luns
### Network ###
network --device=enp2s0 --bootproto=dhcp
network --hostname=localtest.redhat.com

### Partitioning ###
ignoredisk --drives=sda
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=1024
part pv.01 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000023 --size=1 --grow
part pv.03 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000024 --size=1 --grow
volgroup rhvh pv.01 pv.02 pv.03 --reserved-percent=2
logvol swap --fstype=swap --name=swap --vgname=rhvh --recommended
logvol none --name=pool --vgname=rhvh --thinpool --size=300000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=200000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import commands
import os
    
AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_iscsi_01.json')

os.mkdir(AUTO_TEST_DIR)
    
#run ip cmd to get nic status during installation
cmd = "nmcli -t -f DEVICE,STATE dev |grep 'enp6s1f0:connected'"
status = commands.getstatusoutput(cmd)[0]
    
expected_data = {}

expected_data['partition'] = {
    'bootdevice': '/dev/mapper/36005076300810b3e0000000000000022'
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/mpatha1',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000022p1',        
        'fstype': 'ext4',
        'recommended': True
    },
    'volgroup': {
        'lvm': True,
        'name': 'rhvh',
        'reserved-percent': 2
    },
    'swap': {
        'lvm': True,
        'name': 'swap',
        'recommended': True
    },
    'pool': {
        'lvm': True,
        'name': 'pool',
        'size': '300000',
        'grow': True
    },
    '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'size': '200000',
        'grow': True,
        'discard': True
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'size': '20000',
        'discard': True
    },
    '/var/log': {
        'lvm': True,
        'name': 'var_log',
        'fstype': 'ext4',
        'size': '8192',
        'discard': True
    },
    '/var/log/audit': {
        'lvm': True,
        'name': 'var_log_audit',
        'fstype': 'ext4',
        'size': '2048',
        'discard': True
    },
    '/tmp': {
        'lvm': True,
        'name': 'tmp',
        'fstype': 'ext4',
        'size': '1024',
        'discard': True
    },
    '/home': {
        'lvm': True,
        'name': 'home',
        'fstype': 'ext4',
        'size': '1024',
        'discard': True
    },
    '/var/crash': {
        'lvm': True,
        'name': 'var_crash',
        'fstype': 'ext4',
        'size': '10240',
        'discard': True
    }
}

with open(EXPECTED_DATA_FILE, 'wb') as json_file:
    json_file.write(
        json.dumps(
            expected_data, indent=4))

ES
}

coverage_check(){
easy_install coverage
cd /usr/lib/python2.7/site-packages/
coverage run -p -m --branch --source=imgbased imgbased layout --init
mkdir /boot/coverage
cp .coverage* /boot/coverage
}

coverage_check
#imgbase layout --init
compose_expected_data
%end
