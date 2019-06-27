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
#auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, but only use the big local disk
### Network ###
network --device=enp2s0 --bootproto=dhcp
network --hostname=ati-local-02.test.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###
### Post deal ###
%post --erroronfail
imgbase layout --init
%end
