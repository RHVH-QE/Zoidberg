import subprocess
import re


class CleanDisks(object):
    '''
    '''

    def __init__(self):
        self._vg_list = None
        self._pv_list = None
        self._lsblk = None

    def _get_vgs(self):
        # To get vg name
        try:
            cmd = "vgs -o vg_name --noheadings"
            output = subprocess.check_output(
                cmd, shell=True, universal_newlines=True)
            self._vg_list = [x.strip() for x in output.splitlines()]
            print("vg list is {}".format(self._vg_list))
        except Exception as e:
            pass

    def _get_pvs(self):
        try:
            cmd = "pvs -o pv_name --noheadings"
            output = subprocess.check_output(
                cmd, shell=True, universal_newlines=True)
            self._pv_list = [x.strip() for x in output.splitlines()]
            print("pv list is {}".format(self._pv_list))
        except Exception as e:
            pass

    def _remove_vgs(self):
        self._get_vgs()
        for vg in self._vg_list:
            try:
                cmd = "vgremove -f {}".format(vg)
                subprocess.check_output(cmd, shell=True)
            except Exception as e:
                pass

    def _remove_pvs(self):
        self._get_pvs()
        for pv in self._pv_list:
            try:
                cmd = "pvremove -y {}".format(pv)
                subprocess.check_output(cmd, shell=True)
            except Exception as e:
                pass

    def _get_lsblk(self):
        try:
            cmd = "lsblk -rp -o NAME,TYPE --noheadings | grep -E 'disk|mpath|part' | sort -n | uniq"
            output = subprocess.check_output(
                cmd, shell=True, universal_newlines=True)
            self._lsblk = [x.strip() for x in output.splitlines()]
        except Exception as e:
            pass

    def _zero_mbr(self, dev):
        try:
            cmd = "dd if=/dev/zero of={dev} bs=512 count=1".format(dev=dev)
            output = subprocess.check_output(
                cmd, shell=True, universal_newlines=True)
            print("{}\n{}".format(cmd, output))
        except Exception as e:
            pass

    def _clear_part(self, part):
        try:
            cmd = "dd if=/dev/zero of={part} bs=1M count=1".format(part=part)
            output = subprocess.check_output(
                cmd, shell=True, universal_newlines=True)
            print("{}\n{}".format(cmd, output))
        except Exception as e:
            pass

    def _dd_disks(self, clear_part_flag=True):
        self._get_lsblk()
        for part in self._lsblk:
            dev, typ = part.split()
            if typ in ["disk", "mpath"]:
                self._zero_mbr(dev)
            else:
                if clear_part_flag:
                    self._clear_part(dev)

    def clean_in_pre(self):
        self._remove_vgs()
        self._remove_pvs()
        self._dd_disks(clear_part_flag=False)

    def clean_in_post(self):
        self._dd_disks()


if __name__ == '__main__':
    clean = CleanDisks()
    clean.clean_in_pre()
