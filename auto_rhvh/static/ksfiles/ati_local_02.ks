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

### Misc ###
services --enabled=sshd

### Installation mode ###
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.148.42:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per740-28
### Network ###
network --device=eno1 --bootproto=dhcp
network --hostname=ati-local-02.test.redhat.com

### Partitioning ###
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --size=1 --grow
volgroup rhvh pv.01 --reserved-percent=20
logvol swap --fstype=swap --name=swap --vgname=rhvh --recommended
logvol none --name=pool --vgname=rhvh --thinpool --size=40000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=6000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=15360
logvol /var/log --fstype=ext4 --name=var_log --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=8192
logvol /var/log/audit --fstype=ext4 --name=var_log_audit --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=2048
logvol /home --fstype=ext4 --name=home --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=1024
logvol /tmp --fstype=ext4 --name=tmp --vgname=rhvh --thin --poolname=pool --fsoptions="defaults,discard" --size=1024

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
