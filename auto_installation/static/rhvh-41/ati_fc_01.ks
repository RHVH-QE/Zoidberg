### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###

### Security ###

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd
selinux --enforcing

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=em2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=p1p1,p1p2 --bondopts=mode=active-backup,primary=p1p1,miimon=100 --vlanid=50
network --hostname=fctest.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244,/dev/disk/by-id/scsi-36005076300810b3e0000000000000270
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

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

checkdata_map['network'] = {
    'bond': {
        'DEVICE': 'bond0',
        'TYPE': 'Bond',
        'BONDING_OPTS': 'mode=active-backup primary=p1p1 miimon=100',
        'ONBOOT': 'yes',
        'slaves': ['p1p1', 'p1p2']
    },
    'vlan': {
        'DEVICE': 'bond0.50',
        'TYPE': 'Vlan',
        'BOOTPROTO': 'dhcp',
        'VLAN_ID': '50',
        'ONBOOT': 'yes'
    }
}

output = commands.getoutput('vgs --noheadings -o vg_name')
checkdata_map['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/mpatha1',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000022p1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'volgroup': {
        'lvm': True,
        'name': output.strip()
    },
   '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'size': '6144',
        'grow': True
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'size': '15360'
    },
    'pool_meta': {
        'lvm': True,
        'name': 'pool00_tmeta',
        'size': '1024'
    },
    '/var/log': {
        'lvm': True,
        'name': 'var_log',
        'fstype': 'ext4',
        'size': '8192'
    },
    '/var/log/audit': {
        'lvm': True,
        'name': 'var_log_audit',
        'fstype': 'ext4',
        'size': '2048'
    },
    '/tmp': {
        'lvm': True,
        'name': 'tmp',
        'fstype': 'ext4',
        'size': '1024'
    },
    '/home': {
        'lvm': True,
        'name': 'home',
        'fstype': 'ext4',
        'size': '1024'
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
