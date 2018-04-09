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

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, use the iSCSI luns
### Network ###
network --device=em2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=p3p1,p3p2 --bondopts=mode=active-backup,primary=p3p1,miimon=100
network --hostname=ati_iscsi_01.test.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36b8ca3a0e7899a001dfd500516473f47
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d745551 --size=1 --grow
part pv.03 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d736d45 --size=1 --grow
volgroup rhvh pv.01 pv.02 pv.03 --reserved-percent=2
logvol swap --fstype=swap --name=swap --vgname=rhvh --recommended
logvol none --name=pool --vgname=rhvh --thinpool --size=300000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=200000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=20000

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import os
    
AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_iscsi_01.json')

os.mkdir(AUTO_TEST_DIR)
    
expected_data = {}

expected_data['network'] = {
    'bond': {
        'DEVICE': 'bond0',
        'TYPE': 'Bond',
        'BONDING_OPTS': 'mode=active-backup primary=p3p1 miimon=100',
        'ONBOOT': 'yes',
        'slaves': ['p3p1', 'p3p2']
    }
}

expected_data['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/360a9800050334c33424b41762d726954p1',
        'device_wwid': '/dev/mapper/360a9800050334c33424b41762d726954p1',
        'fstype': 'ext4',
        'size': 1024
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

imgbase layout --init
compose_expected_data
%end
