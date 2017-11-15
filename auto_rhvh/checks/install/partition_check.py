import attr
import re


@attr.s
class PartitionCheck(object):
    """
    """
    remotecmd = attr.ib()
    expected_partition = attr.ib()

    def _check_recommended_swap_size(self):
        cmd = "free -g | grep Mem | sed -r 's/\s*Mem:\s*([0-9]+)\s*.*/\\1/'"
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            memtotal = int(ret[1])
        else:
            return False

        cmd = "free -g |grep Swap | sed -r 's/\s*Swap:\s*([0-9]+)\s*.*/\\1/'"
        ret = self.remotecmd.run_cmd(cmd, timeout=300)
        if ret[0]:
            swap = int(ret[1])
        else:
            return False

        if memtotal < 2:
            if int(round(float(swap) / float(memtotal))) != 2:
                return False
        elif memtotal < 8:
            # the mem size calculation algorithm is not just get value from 'free' cmd
            # ignore swap size comparison when mem size in 2 to 8 Gib.
            # if swap != memtotal:
            # return False
            return True
        elif memtotal < 64:
            if int(round(float(memtotal) / float(swap))) != 2:
                return False
        else:
            if swap != 4:
                return False

        return True

    def _check_parts_mnt_fstype(self):
        partition = self.expected_partition
        volgroup = partition.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')
            lvpre = '/dev/mapper/{}'.format(vgname.replace('-', '--'))

        df_patterns = []
        for key in partition:
            if key in ['pool', 'pool_meta', 'swap', 'volgroup', 'bootdevice']:
                continue

            part = partition.get(key)
            fstype = part.get('fstype')
            if part.get('lvm'):
                name = part.get('name')
                if key == '/':
                    pattern = r'^{}-rhvh.*{}.*{}'.format(lvpre, fstype, key)
                else:
                    pattern = r'^{}-{}.*{}.*{}'.format(
                        lvpre, name.replace('-', '--'), fstype, key)
            else:
                part_device = part.get('device_alias')
                pattern = r'^{}.*{}.*{}'.format(part_device, fstype, key)

            df_patterns.append(pattern)

        return self.remotecmd.match_strs_in_cmd_output(
            'df -Th', df_patterns, timeout=300)

    def _check_parts_size(self):
        partition = self.expected_partition
        volgroup = partition.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')

        for key in partition:
            if key in ['volgroup']:
                continue

            part = partition.get(key)
            if part.get('lvm'):
                if part.get('percent'):
                    cmd = 'python -c "print int(' \
                        "round($(lvs --noheadings -o size --unit=m --nosuffix {}/{}) * 100 / " \
                        '$(vgs --noheadings -o size --unit=m --nosuffix {})))"'.format(
                            vgname, part.get('name'), vgname)
                else:
                    cmd = "lvs --noheadings -o size --unit=m --nosuffix {}/{} | sed -r 's/\s*([0-9]+)\..*/\\1/'".format(
                        vgname, part.get('name'))
            else:
                cmd = "expr $(fdisk -s {}) / 1024".format(
                    part.get('device_wwid'))

            ret = self.remotecmd.run_cmd(cmd, timeout=300)

            if ret[0]:
                for line in ret[1].split('\r\n'):
                    if re.match(r'\d+$', line):
                        part_real_size = int(line.strip())
                        break
                else:
                    return False
            else:
                return False

            if part.get('grow'):
                if part_real_size <= int(part.get('size')):
                    return False
                else:
                    maxsize = part.get('maxsize')
                    if maxsize and part_real_size > int(maxsize):
                        return False
            elif part.get('recommended'):
                if key == 'swap':
                    if not self._check_recommended_swap_size():
                        return False
                elif key == '/boot':
                    if part_real_size != 1024:
                        return False
                else:
                    return False
            else:
                if part_real_size != int(part.get('size')):
                    return False

        return True

    def _check_parts_label(self):
        partition = self.expected_partition
        volgroup = partition.get('volgroup')
        if volgroup:
            vgname = volgroup.get('name')

        for key in partition:
            if key in ['volgroup']:
                continue

            part = partition.get(key)
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

    def partition_check(self):
        ck01 = self._check_parts_mnt_fstype()
        ck02 = self._check_parts_size()
        # ck03 = self._check_parts_label()

        return ck01 and ck02

    def bootloader_check(self):
        boot_device = self.expected_partition.get('bootdevice')
        cmd = 'dd if={} bs=512 count=1 2>&1 | strings |grep -i grub'.format(
            boot_device)

        return self.remotecmd.check_strs_in_cmd_output(cmd, ['GRUB'], timeout=300)
