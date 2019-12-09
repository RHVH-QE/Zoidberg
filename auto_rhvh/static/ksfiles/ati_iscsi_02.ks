### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###
%addon com_redhat_kdump --disable
%end

### Security ###

### User ###
rootpw --plaintext redhat

### Misc ###
services --enabled=sshd
selinux --permissive

### Installation mode ###
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per515-01, which is a multipath iSCSI machine, use the iSCSI luns
### Network ###
network --device=eno2 --bootproto=static --ip=10.73.74.201 --netmask=255.255.252.0 --gateway=10.73.75.254 --ipv6=2620:52:0:4948:a9e:1ff:fe63:2cb3/64
network --device=eno1 --bootproto=dhcp --activate --onboot=no
network --device=enp2s0f0 --bootproto=dhcp --vlanid=50
network --hostname=ati_iscsi_02.test.redhat.com

### Partitioning ###
#ignoredisk --drives=/dev/disk/by-id/scsi-36b8ca3a0e7899a001dfd500516473f47
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=1024
part swap --fstype=swap --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d745551 --recommended
part /std_data --fstype=xfs --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=5000 --grow --maxsize=10000
part pv.01 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d726954 --size=1 --grow
part pv.02 --ondisk=/dev/disk/by-id/scsi-360a9800050334c33424b41762d736d45 --size=1 --grow
volgroup rhvh pv.01 pv.02 --reserved-percent=2
logvol /lv_data --fstype=xfs --name=lv_data --vgname=rhvh --size=5000 --grow --maxsize=10000
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=100000 --grow
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=5000 --fsoptions="discard"
logvol /var/crash --fstype=xfs --name=var_crash --vgname=rhvh --thin --poolname=pool --size=20000 --fsoptions="discard"
logvol /thin_data --fstype=xfs --name=thin_data --vgname=rhvh --thin --poolname=pool --size=5000 --grow --maxsize=10000 --fsoptions="discard"

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
nmcli -t -f DEVICE,STATE dev |grep 'eno1:connected'
if [ $? -eq 0 ]; then
    touch /boot/nicup
fi
%end
