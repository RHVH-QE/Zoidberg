### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard us

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
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170202.0/redhat-virtualization-host-4.1-20170202.0.x86_64.liveimg.squashfs
text
reboot

### Network ###
network --onboot=on --bootproto=static --device=enp2s0 --ip=10.66.148.9 --netmask=255.255.252.0 --gateway=10.66.151.254 --hostname=test.redhat.com

### Partitioning ###
ignoredisk --only-use=disk/by-id/ata-WDC_WD2502ABYS-18B7A0_WD-WCAT19563677
zerombr
clearpart --all
bootloader --location=mbr
part /boot --fstype=ext4 --size=1024
part pv.01 --size 20000 --grow
volgroup rhvh pv.01
logvol swap --fstype=swap --name=swap --vgname=rhvh --size=8000
logvol none --name=pool --vgname=rhvh --thinpool --size=200000 --grow
logvol / --fstype=ext4 --name=root --vgname=rhvh --thin --poolname=pool --size=130000
logvol /var --fstype=ext4 --name=var --vgname=rhvh --thin --poolname=pool --size=15360
logvol /home --fstype=xfs --name=home --vgname=rhvh --thin --poolname=pool --size=50000

### Pre deal ###
%pre --erroronfail
dd if=/dev/zero of=/dev/disk/by-id/ata-WDC_WD2502ABYS-18B7A0_WD-WCAT19563677 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/ata-WDC_WD2502ABYS-18B7A0_WD-WCAT19563677-part1 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/ata-WDC_WD2502ABYS-18B7A0_WD-WCAT19563677-part2 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000002 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000002-part1 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000002-part2 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000003 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000003-part1 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000004 bs=512 count=1
dd if=/dev/zero of=/dev/disk/by-id/scsi-36005076300810b3e0000000000000004-part1 bs=512 count=1
%end

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
