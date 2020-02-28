### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=de --xlayouts='de'

### Kdump ###

### Security ###

### User ###
rootpw --plaintext redhat

### Misc ###
services --enabled=sshd

### Installation mode ###
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per740-28
### Network ###
network --device=eno1 --bootproto=dhcp
network --hostname=ati-local-01.test.redhat.com

### Partitioning ###
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --size=200000
volgroup rhvh pv.01
## percent size= (vgsize -  all explicitly defined sizes) * percent / 1024
## swap size = (200000 - 100000) * 5% / 1024 = 4.88G
## / size = (200000 - 100000) * 50% / 1024 = 48.82G
## /var size = (200000 - 100000) * 20% / 1024 = 19.53G
logvol swap --fstype=swap --name=swap --vgname=rhvh --percent=5
logvol none --name=pool --vgname=rhvh --thinpool --size=100000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --percent=50
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --percent=20

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
