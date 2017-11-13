### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=ge --xlayouts='ge'

### Kdump ###

### Security ###

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd
selinux --permissive

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=enp2s0 --bootproto=static --ip=10.66.148.9 --netmask=255.255.252.0 --gateway=10.66.151.254 --ipv6=2620:52:0:4294:222:19ff:fe27:54c7/64
network --hostname=localtest.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size=200000
volgroup rhvh pv.01
logvol swap --fstype=swap --name=swap --vgname=rhvh --percent=5
logvol none --name=pool --vgname=rhvh --thinpool --size=1 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --percent=85
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --percent=10

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import commands
import os
    
AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_local_02.json')

os.mkdir(AUTO_TEST_DIR)
    
expected_data = {}

expected_data['keyboard'] = {'vckeymap': 'ge', 'xlayouts': 'ge'}
expected_data['selinux'] = 'permissive'

expected_data['network'] = {
    'static': {
        'DEVICE': 'enp2s0',
        'BOOTPROTO': 'static',
        'IPADDR': '10.66.148.9',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.66.151.254',
        'IPV6ADDR': '2620:52:0:4294:222:19ff:fe27:54c7/64'
    }
}

expected_data['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/sda1',
        'device_wwid': '/dev/sda1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'volgroup': {
        'lvm': True,
        'name': 'rhvh',
        'size': '200000'
    },
    'pool': {
        'lvm': True,
        'name': 'pool',
        'size': '1',
        'grow': True
    },
    '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'percent': True,
        'size': '85'
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'percent': True,
        'size': '10'
    },
    'swap': {
        'lvm': True,
        'name': 'swap',
        'percent': True,
        'size': '5'
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
