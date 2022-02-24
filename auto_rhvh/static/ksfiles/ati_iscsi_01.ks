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
firewall --disabled
selinux --disabled

### Installation mode ###
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.148.42:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, use the iSCSI luns
### Network ###
network --device=eno2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=enp1s0f0,enp1s0f1 --bondopts=mode=active-backup,primary=enp1s0f0,miimon=100
network --hostname=ati-iscsi-01.test.redhat.com

### Partitioning ###
#ignoredisk --drives=/dev/disk/by-id/scsi-36b8ca3a0e7899a001dfd500516473f47
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --ondisk=/dev/disk/by-id/scsi-360a98000383034384c5d4f4352343763 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-360a98000383034384c5d4f4352343761 --size=1 --grow
part pv.03 --ondisk=/dev/disk/by-id/scsi-360a98000383034384c5d4f4352343765 --size=1 --grow
volgroup rhvh pv.01 pv.02 pv.03 --reserved-percent=2
logvol swap --fstype=swap --name=swap --vgname=rhvh --recommended
logvol none --name=pool --vgname=rhvh --thinpool --size=300000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=200000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=20000

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
grubby --args=crashkernel=250 --update-kernel 0
%end
