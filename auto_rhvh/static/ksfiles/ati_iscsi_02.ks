### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###
%addon com_redhat_kdump --disable
%end

### Security ###

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd
selinux --permissive

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, use the iSCSI luns
### Network ###
network --device=em2 --bootproto=dhcp
#network --device=bond0 --bootproto=dhcp --bondslaves=em1,em2 --bondopts=mode=active-backup,primary=em2,miimon=100
network --device=p2p1 --bootproto=dhcp --vlanid=50
network --hostname=ati_iscsi_02.test.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36b8ca3a0e7899a001dfd500516473f47,/dev/disk/by-id/scsi-360a9800050334c33424b4a4b306a2d66
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=1024
part swap --fstype=swap --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d745551 --recommended
part /std_data --fstype=xfs --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=5000 --grow --maxsize=10000
part pv.01 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d736d45 --size=1 --grow
volgroup rhvh pv.01 pv.02 --reserved-percent=2
logvol /lv_data --fstype=xfs --name=lv_data --vgname=rhvh --size=5000 --grow --maxsize=10000
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=100000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=5000 --fsoptions="discard"
logvol /var/crash --fstype=xfs --name=var_crash --vgname=rhvh --thin --poolname=pool --size=20000 --fsoptions="discard"
logvol /thin_data --fstype=xfs --name=thin_data --vgname=rhvh --thin --poolname=pool --size=5000 --grow --maxsize=10000 --fsoptions="discard"

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import os
    
AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_iscsi_02.json')

os.mkdir(AUTO_TEST_DIR)
    
expected_data = {}

expected_data['selinux'] = 'permissive'

expected_data['network'] = {
    'vlan': {
        'DEVICE': 'p2p1.50',
        'TYPE': 'Vlan',
        'BOOTPROTO': 'dhcp',
        'VLAN_ID': '50',
        'ONBOOT': 'yes'
    }
}

expected_data['partition'] = {
    'bootdevice': '/dev/mapper/360a9800050334c33424b41762d726954',
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/360a9800050334c33424b41762d726954p1',
        'device_wwid': '/dev/mapper/360a9800050334c33424b41762d726954p1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'swap': {
        'lvm': False,
        'device_alias': '/dev/mapper/360a9800050334c33424b41762d745551p1',
        'device_wwid': '/dev/mapper/360a9800050334c33424b41762d745551p1',
        'recommended': True
    },
    '/std_data': {
        'lvm': False,
        'device_alias': '/dev/mapper/360a9800050334c33424b41762d726954p2',
        'device_wwid': '/dev/mapper/360a9800050334c33424b41762d726954p2',
        'fstype': 'xfs',
        'size': '5000',
        'grow': True,
        'maxsize': '10000'
    },
    'volgroup': {
        'lvm': True,
        'name': 'rhvh'
    },
    '/lv_data': {
        'lvm': True,
        'name': 'lv_data',
        'fstype': 'xfs',
        'size': '5000',
        'grow': True,
        'maxsize': '10000',
        'discard': False
    },    
    '/home': {
        'lvm': True,
        'name': 'home',
        'fstype': 'xfs',
        'size': '5000',
        'discard': True
    },
    '/var/crash': {
        'lvm': True,
        'name': 'var_crash',
        'fstype': 'xfs',
        'size': '20000',
        'discard': True
    },
    '/thin_data': {
        'lvm': True,
        'name': 'thin_data',
        'fstype': 'xfs',
        'size': '5000',
        'grow': True,
        'maxsize': '10000',
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
