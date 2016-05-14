
liveimg --url=http://10.66.10.22:8090/rhevh/rhevh7-ng-36/rhev-hypervisor7-ng-3.6-20160506.0/rhev-hypervisor7-ng-3.6-20160506.0.x86_64.liveimg.squashfs

clearpart --all

autopart --type=thinp

rootpw --plaintext redhat

timezone --utc Asia/Harbin

zerombr

text

reboot

%post --erroronfail
imgbase layout --init
imgbase --experimental volume --create /var 4G
%end

%post --nochroot --log=/tmp/auto.log
curl -s http://10.66.9.216:5000/done/dell-per510-01.lab.eng.pek2.redhat.com
%end
