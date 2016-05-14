
liveimg --url={liveimg_url}

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
curl -s http://{srv_ip}:{srv_port}/done/{bkr_name}
%end
