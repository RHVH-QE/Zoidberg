#
# KS for upgrade iscsi test on dell-per515-01
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
#auth --enableshadow --passalgo=md5

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
network --device=eno2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=enp1s0f0,enp1s0f1 --bondopts=mode=active-backup,primary=enp1s0f0,miimon=100

### Partitioning ###
#ignoredisk --only-use=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail

imgbase layout --init
%end