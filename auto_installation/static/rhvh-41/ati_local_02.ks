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
compose_check_data(){
python << ES
import pickle
import commands
import os
    
REMOTE_TMP_FILE_DIR = '/boot/autotest'
    
CHECKDATA_MAP_PKL = 'checkdata_map.pkl'
REMOTE_CHECKDATA_MAP_PKL = os.path.join(REMOTE_TMP_FILE_DIR, CHECKDATA_MAP_PKL)
    
os.mkdir(REMOTE_TMP_FILE_DIR)
    
checkdata_map = {}

checkdata_map['keyboard'] = {'vckeymap': 'ge', 'xlayouts': 'ge'}
checkdata_map['selinux'] = 'permissive'

checkdata_map['network'] = {
    'static': {
        'DEVICE': 'enp2s0',
        'BOOTPROTO': 'static',
        'IPADDR': '10.66.148.9',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.66.151.254',
        'IPV6ADDR': '2620:52:0:4294:222:19ff:fe27:54c7/64'
    }
}

checkdata_map['partition'] = {
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

fp = open(REMOTE_CHECKDATA_MAP_PKL, 'wb')
pickle.dump(checkdata_map, fp)
fp.close()
ES
}

coverage_check(){
cd /tmp
curl -o coveragepy-master.zip http://10.73.73.23:7788/coveragepy-master.zip
unzip coveragepy-master.zip
cd coveragepy-master
python setup.py install
cd /usr/lib/python2.7/site-packages/
coverage run -p -m --branch --source=imgbased imgbased layout --init
mkdir /boot/coverage
cp .coverage* /boot/coverage
}

coverage_check
#imgbase layout --init
compose_check_data
%end
