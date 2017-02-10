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

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --onboot=on --bootproto=dhcp --device=em2
network --onboot=on --bootproto=dhcp --device=bond0 --bondslaves=p1p1,p1p2 --bondopts=mode=active-backup,primary=p1p1,miimon=100 --vlanid=50
network --hostname=test.redhat.com

### Partitioning ###
ignoredisk --drives=disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end

%post --erroronfail --interpreter=/usr/bin/python
import pickle

checkdata_map = {}

checkdata_map['network'] = {
    'bond': {
        'device': 'bond0',
        'slaves': ['p1p1', 'p1p2'],
        'opts': 'mode=active-backup primary=p1p1 miimon=100',
        'onboot': 'yes'
    },
    'vlan': {
        'device': 'bond0.50',
        'id': '50',
        'onboot': 'yes'       
    }
}
checkdata_map['boot'] = {
    'device': '/dev/mapper/mpatha1',
    'size': '1024'
}
checkdata_map['volgroup'] = {'name': 'rhvh_test'}

fp = open('/boot/checkdata_map.pkl', 'wb')
pickle.dump(checkdata_map, fp)
fp.close()
%end
