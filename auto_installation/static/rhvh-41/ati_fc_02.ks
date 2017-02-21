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
auth --enableshadow --passalgo=md5
user --name=test --password=redhat --plaintext

### Misc ###
services --enabled=sshd
firewall --enabled
selinux --disabled

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --bootproto=static --device=em2 --ip=10.73.75.58 --netmask=255.255.252.0 --gateway=10.73.75.254
network --bootproto=dhcp --device=em1
network --bootproto=dhcp --device=bond0 --bondslaves=p1p1,p1p2 --bondopts=mode=balance-rr,miimon=100 --vlanid=50
network --hostname=test.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000023 --size=1 --grow
part pv.03 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000024 --size=1 --grow
volgroup rhvh pv.01 pv.02 pv.03
logvol swap --fstype=swap --name=swap --vgname=rhvh --recommended
logvol none --name=pool --vgname=rhvh --thinpool --size=300000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=300000
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=20000 --grow --maxsize=50000

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

checkdata_map['ntpservers'] = 'clock02.util.phx2.redhat.com'
checkdata_map['user'] = {'name': 'test'}
checkdata_map['selinux'] = 'disabled'

checkdata_map['network'] = {
    'static': {
        'DEVICE': 'em2',
        'BOOTPROTO': 'static',
        'IPADDR': '10.73.75.58',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.73.75.254',
        'ONBOOT': 'yes'
    },
    'dhcp': {
        'DEVICE': 'em1',
        'BOOTPROTO': 'dhcp',
        'ONBOOT': 'yes'
    },
    'bond': {
        'DEVICE': 'bond0',
        'TYPE': 'Bond',
        'BONDING_OPTS': 'mode=balance-rr miimon=100',
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

checkdata_map['partition'] = {
    '/boot': {
        'lvm': False,
        'drive': '/dev/mapper/mpatha',
        'partnum': '1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'volgroup': {
        'lvm': True,
        'name': 'rhvh'
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
        'size': '300000'
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'size': '15360'
    },
    '/home': {
        'lvm': True,
        'name': 'home',
        'fstype': 'xfs',
        'size': '20000',
        'grow': True,
        'maxsize': '50000'
    },
    'swap': {
        'lvm': True,
        'name': 'swap',
        'recommended': True
    }
}

checkdata_map['grubby'] = 'crashkernel=250'

fp = open(REMOTE_CHECKDATA_MAP_PKL, 'wb')
pickle.dump(checkdata_map, fp)
fp.close()
ES
}

grubby_test(){
kernel=$(grubby --info=0 | grep '^kernel')
kernel=${kernel#*=}
grubby --args=crashkernel=250 --update-kernel $kernel
}

imgbase layout --init
grubby_test
compose_check_data
%end
