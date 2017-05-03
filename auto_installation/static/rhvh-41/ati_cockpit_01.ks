
liveimg --url=http://10.66.10.22:8090/rhvh_ngn/squashimg/redhat-virtualization-host-4.1-20170331.0/redhat-virtualization-host-4.1-20170331.0.x86_64.liveimg.squashfs

clearpart --all

autopart --type=thinp

rootpw --plaintext redhat

timezone --utc Asia/Harbin

zerombr

text

reboot

%post --erroronfail
compose_check_data(){
python << ES
import pickle
import commands
import os
    
#define filename and dirs
REMOTE_TMP_FILE_DIR = '/boot/autotest'
    
CHECKDATA_MAP_PKL = 'checkdata_map.pkl'
REMOTE_CHECKDATA_MAP_PKL = os.path.join(REMOTE_TMP_FILE_DIR, CHECKDATA_MAP_PKL)
    
#create autotest dir under /boot
os.mkdir(REMOTE_TMP_FILE_DIR)
    
#run ip cmd to get nic status during installation
cmd = "nmcli -t -f DEVICE,STATE dev |grep 'enp6s1f0:connected'"
status = commands.getstatusoutput(cmd)[0]
    
#compose checkdata_map and write it to the pickle file
checkdata_map = {}

checkdata_map['lang'] = 'en_US.UTF-8'
checkdata_map['timezone'] = 'Asia/Shanghai'
checkdata_map['ntpservers'] = 'clock02.util.phx2.redhat.com'
checkdata_map['keyboard'] = {'vckeymap': 'us', 'xlayouts': 'us'}
checkdata_map['kdump'] = {'reserve-mb': '200'}
checkdata_map['user'] = {'name': 'test'}

checkdata_map['network'] = {
    'static': {
        'DEVICE': 'enp2s0',
        'BOOTPROTO': 'static',
        'IPADDR': '10.66.148.9',
        'NETMASK': '255.255.252.0',
        'GATEWAY': '10.66.151.254',
        'ONBOOT': 'yes'
    },
    'nic': {
        'DEVICE': 'enp6s1f0',
        'BOOTPROTO': 'dhcp',
        'status': status,
        'ONBOOT': 'no'
    },
    'hostname': 'localtest.redhat.com'
}

checkdata_map['partition'] = {
    '/boot': {
        'lvm': False,
        'device_alias': '/dev/sda1',
        'device_wwid': '/dev/sda1',
        'fstype': 'ext4',
        'size': '1024'
    },
    'volgroup': {
        'lvm': True,
        'name': 'rhvh'
    },
    'pool': {
        'lvm': True,
        'name': 'pool',
        'size': '200000',
        'grow': True
    },
    '/': {
        'lvm': True,
        'name': 'root',
        'fstype': 'ext4',
        'size': '130000'
    },
    '/var': {
        'lvm': True,
        'name': 'var',
        'fstype': 'ext4',
        'size': '15360'
    },
    '/home': {
        'lvm': True,
        'name': 'home',
        'fstype': 'xfs',
        'size': '50000'
    },
    'swap': {
        'lvm': True,
        'name': 'swap',
        'size': '8000'
    }
}

fp = open(REMOTE_CHECKDATA_MAP_PKL, 'wb')
pickle.dump(checkdata_map, fp)
fp.close()
ES
}

imgbase layout --init
compose_check_data
%end
