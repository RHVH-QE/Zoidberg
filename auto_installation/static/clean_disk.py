import commands
import re


class CleanDisks(object):
    '''
    '''
    def __init__(self):
        self._vg_list = None
        self._sfdisk = None
        self._lsblk = None

    def _get_vgs(self):
        # To get vg name
        cmd = "vgs -o vg_name --noheadings"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print 'Failed to run cmd "%s"' % cmd
        else:
            self._vg_list = [x.strip() for x in output.split('\n')]
            print "vg list is %s" % self._vg_list

    def _remove_vgs(self):
        for vg in self._vg_list:
            cmd = "vgremove -f {}".format(vg)
            commands.getstatusoutput(cmd)

    def _get_sfdisk(self):
        cmd = "sfdisk -d | grep -v 'start=\s*0,'|awk '{if($1 ~/dev/) print $1}{if($5 ~/dev/) print $5}'"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print 'Failed to run cmd "%s".' % cmd
        else:
            self._sfdisk = [x.strip() for x in output.split('\n')]

    def _get_lsblk(self):
        cmd = "lsblk -rp -o NAME,TYPE --noheadings | grep -E 'disk|mpath|part' | sort -n | uniq"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print 'Failed to run cmd "%s".' % cmd
        else:
            self._lsblk = [x.strip() for x in output.split('\n')]

    def _dd_disks(self):
        for part in self._lsblk:
            dev, typ = part.split()
            if dev in self._sfdisk:
                if typ in ["disk", "mpath"]:
                    bs = "512"
                    count = "1"
                else:
                    bs = "1M"
                    count = "1"
                cmd = "dd if=/dev/zero of={dev} bs={bs} count={count}".format(dev=dev, bs=bs, count=count)
                output = commands.getstatusoutput(cmd)[1]
                print "%s\n%s" % (cmd, output)

    def _del_dev_mapper(self):
        # To remove /dev/mapper/*
        cmd = "ls /dev/mapper"
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            print 'Failed to run cmd "%s".' % cmd
            return

        device_list = [x.strip() for x in output.split()]
        for device in device_list:
            if not (re.match(r'live', device) or re.match(r'control', device)):
                cmd = "dmsetup remove /dev/mapper/{} -f".format(device)
                output = commands.getstatusoutput(cmd)[1]
                print "%s\n%s" % (cmd, output)

    def _reboot(self):
        cmd = "reboot"
        commands.getstatusoutput(cmd)

    def clean_disks(self):
        self._get_sfdisk()
        self._get_lsblk()
        self._dd_disks()

if __name__ == '__main__':
    CleanDisks().clean_disks()
