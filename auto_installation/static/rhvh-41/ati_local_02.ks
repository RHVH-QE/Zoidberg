### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard ge

### Kdump ###
%addon com_redhat_kdump --enable --reserve-mb=200
%end

### Security ###
%addon org_fedora_oscap
content-type=scap-security-guide
profile=standard
%end

### User ###
rootpw --plaintext redhat
auth --enableshadow --passalgo=md5
user --name=test --password=redhat --plaintext

### Misc ###
services --enabled=sshd

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --onboot=on --bootproto=static --device=em1 --ip=10.73.73.23 --netmask=255.255.252.0 --gateway=10.73.75.254 --hostname=test.redhat.com

### Partitioning ###
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size 20000 --grow
volgroup test pv.01
logvol none --name=ngn_pool --vgname=test --thinpool --size=200000
logvol / --fstype=ext4 --name=root --vgname=test --thin --poolname=ngn_pool --size=30000 --grow
logvol /var --fstype=ext4 --name=var --vgname=test --thin --poolname=ngn_pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=test --thin --poolname=ngn_pool --size=50000
logvol swap --fstype=swap --name=swap --vgname=test --size=8000

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
