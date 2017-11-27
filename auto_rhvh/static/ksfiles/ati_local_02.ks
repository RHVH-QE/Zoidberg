### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=de --xlayouts='de'

### Kdump ###
%addon com_redhat_kdump --disable
%end

### Security ###

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=sha512

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

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, but only use the big local disk
### Network ###
network --device=em2 --bootproto=dhcp
network --hostname=fctest.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --size=20000 --grow
volgroup rhvh pv.01 --reserved-percent=2
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
import commands
import os

AUTO_TEST_DIR = '/boot/autotest'
EXPECTED_DATA_FILE = os.path.join(AUTO_TEST_DIR, 'ati_fc_02.json')

os.mkdir(AUTO_TEST_DIR)

expected_data = {}

expected_data['keyboard'] = {'vckeymap': 'de', 'xlayouts': 'de'}
expected_data['selinux'] = 'disabled'

expected_data['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/mapper/mpatha1',
        'device_wwid': '/dev/mapper/36005076300810b3e0000000000000022p1',        
        'fstype': 'ext4',
        'size': 1024
    }    
}

expected_data['grubby'] = 'crashkernel=250'

with open(EXPECTED_DATA_FILE, 'wb') as json_file:
    json_file.write(
        json.dumps(
            expected_data, indent=4))

ES
}

grubby_test(){
kernel=$(grubby --info=0 | grep '^kernel')
kernel=${kernel#*=}
grubby --args=crashkernel=250 --update-kernel $kernel
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
grubby_test
compose_expected_data
%end