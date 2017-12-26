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

# This ks is specific to dell-per510-01, which is a multipath FC machine, use the FC luns
### Network ###
network --device=em2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=p1p1,p1p2 --bondopts=mode=active-backup,primary=p1p1,miimon=100 --vlanid=50
network --hostname=ati_fc_01.test.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import commands
import os

AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_fc_01.json')

os.mkdir(AUTO_TEST_DIR)

expected_data = {}

expected_data['network'] = {
    'dhcp': {
        'DEVICE': 'em2',
        'BOOTPROTO': 'dhcp',
        'ONBOOT': 'yes'
    },
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
expected_data['partition'] = {
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
    'swap': {
        'lvm': True,
        'name': 'swap',
        'recommended': True
    },
    'pool_meta': {
        'lvm': True,
        'name': 'pool00_tmeta',
        'size': '1024'
    },    
   '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'size': '6144',
        'grow': True,
        'discard': True
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'size': '15360',
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
mkdir /boot/coverage
export COVERAGE_FILE=/boot/coverage/.coverage.install
coverage run -p -m --branch --source=/usr/lib/python2.7/site-packages/imgbased imgbased layout --init
}

coverage_check
#imgbase layout --init
compose_expected_data
%end
