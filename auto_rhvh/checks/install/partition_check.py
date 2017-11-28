import logging
import attr
import re

log = logging.getLogger('bender')


@attr.s
class PartitionCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_partition = attr.ib()

    def _check_recommended_swap_size(self, swap_size):
        cmd = "free -g | grep Mem | sed -r 's/\s*Mem:\s*([0-9]+)\s*.*/\\1/'"
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            memtotal = int(ret[1])
        else:
            return False
        '''
        cmd = "free -m |grep Swap | sed -r 's/\s*Swap:\s*([0-9]+)\s*.*/\\1/'"
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            swap = int(ret[1])
        else:
            return False
        '''
        swap = swap_size / 1024

        if memtotal < 2:
            if int(round(float(swap) / float(memtotal))) != 2:
                return False
        elif memtotal < 8:
            # the mem size calculation algorithm is not just get value from 'free' cmd
            # ignore swap size comparison when mem size in 2 to 8 Gib.
            if swap != memtotal:
                return False
        elif memtotal < 64:
            if int(round(float(memtotal) / float(swap))) != 2:
                return False
        else:
            if swap != 4:
                return False

        return True

    def _get_part_real_size(self, part, vgname):
        part_real_size = None

        if part.get('lvm'):
            if part.get('percent'):
                cmd = 'python -c "print int(' \
                    "round($(lvs --noheadings -o size --unit=m --nosuffix {}/{}) * 100 / " \
                    '$(vgs --noheadings -o size --unit=m --nosuffix {})))"'.format(
                        vgname, part.get('name'), vgname)
            else:
                cmd = "lvs --noheadings -o size --unit=m --nosuffix {}/{} | " \
                    "sed -r 's/\s*([0-9]+)\..*/\\1/'".format(
                        vgname, part.get('name'))
        else:
            cmd = "expr $(fdisk -s {}) / 1024".format(part.get('device_wwid'))

        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            for line in ret[1].split('\r\n'):
                if re.match(r'\d+$', line):
                    part_real_size = int(line.strip())
                    break

        return part_real_size

    def _check_parts_size(self, partitions):
        volgroup = partitions.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')
        else:
            vgname = None

        for key in partitions:
            if key in ['volgroup', 'bootdevice']:
                continue

            part = partitions.get(key)

            # To get part real size
            part_real_size = self._get_part_real_size(part, vgname)
            if not part_real_size:
                log.error("Failed to get part %s real size.", part.get('name'))
                return False

            # To check whether the part real size is correct
            if part.get('grow'):
                if part_real_size <= int(part.get('size')):
                    log.error("For Part %s, real size %s lower than configured size %s",
                              part.get('name'), str(part_real_size), part.get('size'))
                    return False
                else:
                    maxsize = part.get('maxsize')
                    if maxsize and part_real_size > int(maxsize):
                        log.error("For part %s, real size %s bigger than configured maxsize %s",
                                  part.get('name'), str(part_real_size), maxsize)
                        return False
            elif part.get('recommended'):
                if key == 'swap':
                    if not self._check_recommended_swap_size(part_real_size):
                        return False
            else:
                if part_real_size != int(part.get('size')):
                    log.error("For Part %s, real size %s not equal to configured size %s",
                              part.get('name'), str(part_real_size), part.get('size'))
                    return False

        return True

    def _check_parts_mnt_fstype(self, partitions):
        volgroup = partitions.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')
            lvpre = '/dev/mapper/{}'.format(vgname.replace('-', '--'))

        for key in partitions:
            if key in ['pool', 'pool_meta', 'swap', 'volgroup', 'bootdevice']:
                continue

            part = partitions.get(key)
            fstype = part.get('fstype')

            if part.get('lvm'):
                part_name = part.get('name')
                if key == '/':
                    pattern = r'^{}-rhvh.*{}\s+{}'.format(lvpre, fstype, key)
                else:
                    pattern = r'^{}-{}\s+{}\s+{}'.format(
                        lvpre, part_name.replace('-', '--'), fstype, key)
            else:
                part_device = part.get('device_alias')
                pattern = r'^{}\s+{}\s+{}'.format(part_device, fstype, key)

            cmd = "df --output=source,fstype,target | egrep '{}'".format(
                pattern)
            ret = self.remotecmd.run_cmd(cmd, timeout=300)
            if not ret[0]:
                return False

        return True

    def _check_discard_option(self, partitions):
        for key in partitions:
            part = partitions.get(key)
            if part.get('discard'):
                pattern = r'{}\s+.*discard'.format(key)
                cmd = "mount | egrep '{}'".format(pattern)
                ret = self.remotecmd.run_cmd(cmd, timeout=300)
                if not ret[0]:
                    return False

        return True

    def _check_parts_label(self, partitions):
        volgroup = partitions.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')

        for key in partitions:
            if key in ['volgroup']:
                continue

            part = partitions.get(key)
            label = part.get('label')
            if label:
                if part.get('lvm'):
                    device = "/dev/mapper/{}-{}".format(
                        vgname.replace('-', '--'),
                        part.get('name').replace('-', '--'))
                else:
                    device = part.get('device_wwid')

                cmd = "blkid {}".format(device)
                strs = [part.get('label')]
                ret = self.remotecmd.check_strs_in_cmd_output(
                    cmd, strs, timeout=300)
                if not ret:
                    return False

        return True

    def _check_parts(self, name_list=None):
        partitions = {}
        if not name_list:
            partitions = self.expected_partition
        else:
            for key in name_list:
                value = self.expected_partition.get(key)
                if value:
                    partitions[key] = value

        ck01 = self._check_parts_mnt_fstype(partitions)
        ck02 = self._check_parts_size(partitions)
        ck03 = self._check_discard_option(partitions)

        return ck01 and ck02 and ck03

    def partitions_check(self):
        return self._check_parts()

    def custom_boot_check(self):
        name_list = ['/boot', '/boot/efi', 'biosboot']
        return self._check_parts(name_list)

    def custom_swap_check(self):
        name_list = ['swap', 'volgroup']
        return self._check_parts(name_list)

    def custom_std_data_check(self):
        name_list = ['/std_data']
        return self._check_parts(name_list)

    def custom_lv_data_check(self):
        name_list = ['/lv_data', 'volgroup']
        return self._check_parts(name_list)

    def custom_thin_data_check(self):
        name_list = ['/thin_data', 'volgroup']
        return self._check_parts(name_list)

    def custom_nists_check(self):
        name_list = ['/', '/var', '/var/log',
                     '/var/log/audit', '/home', '/tmp', 'volgroup']
        return self._check_parts(name_list)

    def custom_var_crash_check(self):
        name_list = ['/var/crash', 'volgroup']
        return self._check_parts(name_list)

    def bootloader_check(self):
        boot_device = self.expected_partition.get('bootdevice')
        cmd = 'dd if={} bs=512 count=1 2>&1 | strings | grep -i grub'.format(
            boot_device)

        return self.remotecmd.check_strs_in_cmd_output(cmd, ['GRUB'], timeout=300)

    def vgfree_check(self):
        cmd = "vgs --units=m --rows | grep {name} | sed 's/{name}//' | " \
            "sed -r 's/\s*([0-9]+)\..*/\\1/'"
        cmd1 = cmd.format(name='VSize')
        cmd2 = cmd.format(name='VFree')

        size = []
        for cmd in [cmd1, cmd2]:
            ret = self.remotecmd.run_cmd(cmd, timeout=300)
            if ret[0]:
                size.append(ret[1].strip())
            else:
                return False

        act_percent = round(float(size[1]) * 100 / float(size[0]))
        conf_percent = self.expected_partition.get(
            'volgroup').get('reserved-percent')
        if act_percent != conf_percent:
            log.error('The real reserved percent of volume group is %s, not equal to the configured %s',
                      act_percent, conf_percent)
            return False

        return True
