### KS for rhvm side upgrade vlan+bond test on dell-per515-01

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
#auth --enableshadow --passalgo=md5
user --name=test --password=redhat --plaintext

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.148.42:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
#network --device=eno2 --bootproto=dhcp
#network --device=bond0 --bootproto=dhcp --bondslaves=enp6s0f0,enp6s0f1 --bondopts=mode=active-backup,primary=enp6s0f0,miimon=100 --vlanid=50
network --device=eno2 --bootproto=dhcp

### Partitioning ###
ignoredisk --only-use=/dev/disk/by-id/scsi-360a98000383034384c5d4f4352343763
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
