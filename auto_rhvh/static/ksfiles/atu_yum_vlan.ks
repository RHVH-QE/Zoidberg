### KS for upgrade vlan test on dell-per510-01

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
#auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
#network --device=em2 --bootproto=dhcp
#network --device=p1p1 --bootproto=dhcp --vlanid=50
network --device=eno2 --bootproto=dhcp
network --device=enp6s0f0 --bootproto=dhcp --vlanid=50

### Partitioning ###
#ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
