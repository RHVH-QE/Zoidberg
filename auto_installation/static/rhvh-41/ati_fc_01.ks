### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai

### Keyboard ###
keyboard us

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

### Partitioning ###
ignoredisk --drives=disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###
%pre --erroronfail
dd if=/dev/zero of=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244p1 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244p2 bs=512 count=1
%end

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
