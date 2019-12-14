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

# This ks is specific to Dell PowerEdge R740
### Network ###
network --device=eno1 --bootproto=dhcp
network --hostname=ati_local_01.test.redhat.com

### Partitioning ###
#ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --size=200000
volgroup rhvh pv.01
## percent size= (vgsize -  all explicitly defined sizes) * percent / 1024
## swap size = (200000 - 1 - 50000 - 15000) * 5% / 1024 = 6.59G
## lv_data size = (200000 - 1 - 50000 - 15000) * 10% / 1024 = 13.18G
logvol swap --fstype=swap --name=swap --vgname=rhvh --percent=5
logvol /lv_data --fstype=xfs --name=lv_data --vgname=rhvh --percent=10
logvol none --name=pool --vgname=rhvh --thinpool --size=1 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=50000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15000

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
