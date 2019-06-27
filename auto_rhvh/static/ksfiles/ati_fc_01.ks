### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

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
auth --enableshadow --passalgo=sha512
user --name=test --password=redhat --plaintext

### Misc ###
services --enabled=sshd
selinux --enforcing
firewall --enabled

### Installation mode ###
install
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to dell-per510-01, which is a multipath FC machine, use the FC luns
### Network ###
network --device=em2 --bootproto=dhcp
network --device=bond0 --bootproto=dhcp --bondslaves=p1p1,p1p2 --bondopts=mode=active-backup,primary=p1p1,miimon=100 --vlanid=50
network --hostname=ati-fc-01.test.redhat.com

### Partitioning ###
ignoredisk --drives=/dev/disk/by-id/scsi-36782bcb03cdfa2001ebc7e930f1ca244
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
