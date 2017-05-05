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
auth --enableshadow --passalgo=md5

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
network --device=em1 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=p3p1,p4p1 --bondopts=mode=active-backup,primary=p3p1,miimon=100 --vlanid=20

### Partitioning ###
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
        'slaves': ['p3p1', 'p4p1']
    },
    'vlan': {
        'DEVICE': 'bond0.20',
        'TYPE': 'Vlan',
        'BOOTPROTO': 'dhcp',
        'VLAN_ID': '20',
        'ONBOOT': 'yes'
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
