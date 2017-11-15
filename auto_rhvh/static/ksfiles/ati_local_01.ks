### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###
%addon com_redhat_kdump --enable --reserve-mb=200
%end

### Security ###
%addon org_fedora_oscap
content-type=scap-security-guide
profile=standard
%end

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512
user --name=test --password=redhat --plaintext

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=enp2s0 --bootproto=static --ip=10.66.148.9 --netmask=255.255.252.0 --gateway=10.66.151.254
network --device=enp6s1f0 --bootproto=dhcp --activate --onboot=no
network --hostname=localtest.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size=20000 --grow
volgroup rhvh pv.01 --reserved-percent=5
logvol swap --fstype=swap --name=swap --vgname=rhvh --size=8000
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=130000
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=50000

### Pre deal ###

### Post deal ###
%post --erroronfail
compose_expected_data(){
python << ES
import json
import commands
import os
    
AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_local_01.json')

os.mkdir(AUTO_TEST_DIR)
    
#run ip cmd to get nic status during installation
cmd = "nmcli -t -f DEVICE,STATE dev |grep 'enp6s1f0:connected'"
status = commands.getstatusoutput(cmd)[0]
    
expected_data = {}

expected_data['lang'] = 'en_US.UTF-8'
expected_data['timezone'] = {
    'timezone': 'Asia/Shanghai',
    'ntpservers': 'clock02.util.phx2.redhat.com'
}
expected_data['keyboard'] = {'vckeymap': 'us', 'xlayouts': 'us'}
expected_data['kdump'] = {'reserve-mb': '200'}
expected_data['user'] = {'name': 'test'}

expected_data['network'] = {
    'static': {
        'DEVICE': 'enp2s0',
        'BOOTPROTO': 'static',
        'IPADDR': '10.66.148.9',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.66.151.254',
        'ONBOOT': 'yes'
    },
    'nic': {
        'DEVICE': 'enp6s1f0',
        'BOOTPROTO': 'dhcp',
        'status': status,
        'ONBOOT': 'no'
    },
    'hostname': 'localtest.redhat.com'
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
        'name': 'rhvh'
    },
    'pool': {
        'lvm': True,
        'name': 'pool',
        'size': '200000',
        'grow': True
    },
    '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'size': '130000'
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
        'size': '50000'
    },
    'swap': {
        'lvm': True,
        'name': 'swap',
        'size': '8000'
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
