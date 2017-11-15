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
selinux --enforcing

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=em2 --bootproto=dhcp
#network --device=bond0 --bootproto=dhcp --bondslaves=em1,em2 --bondopts=mode=active-backup,primary=em2 --activate
network --device=p3p2 --bootproto=dhcp --vlanid=50
network --hostname=fctest.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244,/dev/disk/by-id/scsi-36005076300810b3e0000000000000270
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=1024
part swap --fstype=swap --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000024 --recommended
part /data --fstype=xfs --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=5000 --grow --maxsize=10000
part pv.01 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000022 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-36005076300810b3e0000000000000023 --size=1 --grow
volgroup rhvh pv.01 pv.02 --reserved-percent=5
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=100000 --grow
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
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_fc_03.json')

os.mkdir(AUTO_TEST_DIR)
    
expected_data = {}

expected_data['selinux'] = 'enforcing'

expected_data['network'] = {
    'vlan': {
        'DEVICE': 'p3p2.50',
        'TYPE': 'Vlan',
        'BOOTPROTO': 'dhcp',
        'VLAN_ID': '50',
        'ONBOOT': 'yes'
    }
}

expected_data['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/mpatha1',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000022p1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'swap': {
        'lvm': False,
        'device_alias': '/dev/mapper/36005076300810b3e0000000000000024p1',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000024p1',
        'recommended': True
    },
    '/data': {
        'lvm': False,
        'device_alias': '/dev/mapper/mpatha2',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000022p2',
        'fstype': 'xfs',
        'size': '5000',
        'grow': True,
        'maxsize': '10000'
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
