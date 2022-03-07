#
# KS for vdsm vlan anaconda test on dell-per515-01
#
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
selinux --enforcing

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.148.42:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=em2 --bootproto=dhcp
network --device=p2p1 --bootproto=static --ip=192.168.50.48 --netmask=255.255.255.0 --gateway=192.168.50.1 --vlanid=50

### Partitioning ###
ignoredisk --only-use=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail

imgbase layout --init
%end

