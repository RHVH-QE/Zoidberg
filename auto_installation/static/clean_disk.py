import commands
import re


class CleanDisks(object):
    '''
    '''
    def __init__(self):
        self._vg_list = None
        self._pv_list = None
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

    def _get_pvs(self):
        cmd = "pvs -o pv_name --noheadings"
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            print 'Failed to run cmd "%s"' % cmd
        else:
            self._pv_list = [x.strip() for x in output.split('\n')]
            print "pv list is %s" % self._pv_list

    def _remove_vgs(self):
        self._get_vgs()
        for vg in self._vg_list:
            cmd = "vgremove -f {}".format(vg)
            commands.getstatusoutput(cmd)

    def _remove_pvs(self):
        self._get_pvs()
        for pv in self._pv_list:
            cmd = "pvremove -y {}".format(pv)
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

    def _zero_mbr(self, dev):
        cmd = "dd if=/dev/zero of={dev} bs=512 count=1".format(dev=dev)
        output = commands.getstatusoutput(cmd)[1]
        print "%s\n%s" % (cmd, output)

    def _clear_part(self, part):
        cmd = "dd if=/dev/zero of={part} bs=1M count=1".format(part=part)
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

    def _dd_disks(self, flag="all"):
        self._get_sfdisk()
        self._get_lsblk()

        for part in self._lsblk:
            dev, typ = part.split()
            if dev in self._sfdisk:
                if typ in ["disk", "mpath"]:
                    if flag in ["mbr", "all"]:
                        self._zero_mbr(dev)
                else:
                    if flag in ["part", "all"]:
                        self._clear_part(dev)

    def clean_in_pre(self):
        self._remove_vgs()
        self._remove_pvs()
        self._dd_disks(flag="mbr")

    def clean_in_post(self):
        self._dd_disks()

if __name__ == '__main__':
    clean = CleanDisks()
    clean.clean_in_pre()
