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
auth --enableshadow --passalgo=sha512

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will be substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per515-02, which is a single path iSCSI machine, only use the local disk
### Network ###
network --device=em2 --bootproto=static --ip=10.73.75.181 --netmask=255.255.252.0 --gateway=10.73.75.254 --ipv6=2620:52:0:4948:a9e:1ff:fe63:2c6e/64
network --device=em1 --bootproto=dhcp --activate --onboot=no
network --hostname=ati-local-01.test.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
reqpart --add-boot
part pv.01 --size=200000
volgroup rhvh pv.01
logvol swap --fstype=swap --name=swap --vgname=rhvh --percent=5
logvol none --name=pool --vgname=rhvh --thinpool --size=1 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --percent=85
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --percent=10

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
nmcli -t -f DEVICE,STATE dev |grep 'em1:connected'
if [ $? -eq 0 ]; then
    touch /boot/nicup
fi
%end
