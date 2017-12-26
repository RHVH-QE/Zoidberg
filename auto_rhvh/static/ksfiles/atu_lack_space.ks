### KS for upgrade lack space test on dell-pet105-01

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
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --device=enp2s0 --bootproto=dhcp

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size=60000
volgroup rhvh pv.01
logvol swap --fstype=swap --name=swap --vgname=rhvh --size=8000
logvol none --name=pool --vgname=rhvh --thinpool --size=40000
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=6000
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end