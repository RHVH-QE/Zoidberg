### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai

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
network --device=enp2s0 --bootproto=dhcp
network --hostname=test.redhat.com

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

checkdata_map['partition'] = {
    '/boot': {
        'lvm': False,
        'drive': '/dev/sda',
        'partnum': '1',
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

imgbase layout --init
compose_check_data
%end
