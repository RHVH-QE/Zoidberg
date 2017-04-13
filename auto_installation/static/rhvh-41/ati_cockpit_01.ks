
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170331.0/redhat-virtualization-host-4.1-20170331.0.x86_64.liveimg.squashfs

clearpart --all

autopart --type=thinp

rootpw --plaintext redhat

timezone --utc Asia/Harbin

zerombr

text

reboot

%post --erroronfail
imgbase layout --init
%end
