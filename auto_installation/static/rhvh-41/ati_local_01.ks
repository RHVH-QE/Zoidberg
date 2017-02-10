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
network --onboot=on --bootproto=static --device=enp2s0 --ip=10.66.148.9 --netmask=255.255.252.0 --gateway=10.66.151.254 --hostname=test.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size 20000 --grow
volgroup rhvh pv.01
logvol swap --fstype=swap --name=swap --vgname=rhvh --size=8000
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=130000
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=50000

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end

%post --erroronfail --interpreter=/usr/bin/python
import pickle

checkdata_map = {}

checkdata_map['lang'] = 'en_US.UTF-8'
checkdata_map['timezone'] = 'Asia/Shanghai'
checkdata_map['ntpservers'] = 'clock02.util.phx2.redhat.com'
checkdata_map['keyboard'] = {'vckeymap': 'us', 'xlayouts': 'us'}
checkdata_map['kdump'] = {'reserve-mb': '200'}
checkdata_map['user'] = {'name': 'test'}
checkdata_map['network'] = {
    'static': {    
        'device': 'enp2s0',
        'ip': '10.66.148.9',
        'netmask': '255.255.252.0',
        'gateway': '10.66.151.254',
        'onboot': 'yes'
    },
    'hostname': 'test.redhat.com'
}
checkdata_map['boot'] = {
    'device': '/dev/sda1',
    'size': '1024'
}
checkdata_map['volgroup'] = {'name': 'rhvh'}
checkdata_map['logvol'] = {
    'pool': {
        'name': 'pool',
        'size': '200000',
        'grow': True
    },
    '/': {
        'name': 'root',
        'fstype': 'ext4',
        'size': '130000'
    },
    '/var': {
        'name': 'var',
        'fstype': 'ext4',
        'size': '15360'
    },
    '/home': {
        'name': 'home',
        'fstype': 'xfs',
        'size': '50000'
    },
    'swap': {
        'name': 'swap',
        'size': '8000'
    }
}

fp = open('/boot/checkdata_map.pkl', 'wb')
pickle.dump(checkdata_map, fp)
fp.close()
%end
