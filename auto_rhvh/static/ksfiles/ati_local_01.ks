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
selinux --enforcing
firewall --disabled

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-pet105-01, which is a single path iSCSI machine, only use the local disk
### Network ###
network --device=enp2s0 --bootproto=static --ip=10.66.148.9 --netmask=255.255.252.0 --gateway=10.66.151.254 --ipv6=2620:52:0:4294:222:19ff:fe27:54c7/64
network --device=enp6s1f0 --bootproto=dhcp --activate --onboot=no
network --hostname=ati_local_01.test.redhat.com

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
expected_data['selinux'] = 'enforcing'

expected_data['network'] = {
    'static': {
        'DEVICE': 'enp2s0',
        'BOOTPROTO': 'static',
        'IPADDR': '10.66.148.9',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.66.151.254',
        'IPV6ADDR': '2620:52:0:4294:222:19ff:fe27:54c7/64',
        'ONBOOT': 'yes'
    },
    'nic': {
        'DEVICE': 'enp6s1f0',
        'BOOTPROTO': 'dhcp',
        'status': status,
        'ONBOOT': 'no'
    },
    'hostname': 'ati_local_01.test.redhat.com'
}

expected_data['partition'] = {
    'volgroup': {
        'lvm': True,
        'name': 'rhvh'
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
