### Language ###
lang en_US.UTF-8

### Timezone ###
timezone Asia/Shanghai --utc --ntpservers=clock02.util.phx2.redhat.com

### Keyboard ###
keyboard --vckeymap=us --xlayouts='us'

### Kdump ###

### Security ###
%addon org_fedora_oscap
content-type=scap-security-guide
profile=xccdf_org.ssgproject.content_profile_rhvh-stig
%end

### User ###
rootpw --plaintext redhat

### Misc ###
services --enabled=sshd

### Installation mode ###
#liveimg url will substitued by autoframework
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170120.0/redhat-virtualization-host-4.1-20170120.0.x86_64.liveimg.squashfs
text
reboot

# This ks is specific to ibm-x3650m5-05
### Network ###
network --device=eno1 --bootproto=dhcp
network --hostname=ati-ibm-01.test.redhat.com

### Partitioning ###
ignoredisk --only-use=sda
zerombr
clearpart --all
bootloader --location=mbr
autopart --type=thinp

### Pre deal ###

### Post deal ###
%post --erroronfail
imgbase layout --init
%end
