from common import DELL_PER510_01, DELL_PER515_01
from collections import OrderedDict


t_cases = [
    ("RHEVM-24115", ('atv_local-vlani_01.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24151", ('atv_local-vlani_01.ks', DELL_PER515_01, 'create_local_sd_check')),
    ("RHEVM-24188", ('atv_local-vlani_01.ks', DELL_PER515_01, 'fcoe_service_check')),
    ("RHEVM-24116", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24117", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24154", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'create_nfs_sd_check')),
    ("RHEVM-24202", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'create_iso_sd_check')),
    ("RHEVM-24409", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'create_vm_with_disk_check')),
    ("RHEVM-24204", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'vm_life_cycle_check')),
    ("RHEVM-24722", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'delete_vm_check')),
    ("RHEVM-24185", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'maintenance_host_check')),
    ("RHEVM-24189", ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'remove_host_check')),
    # must install host before check
    ("RHEVM-invalid1", ('atv_scsi_01.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24175", ('atv_scsi_01.ks', DELL_PER515_01, 'create_scsi_sd_check')),
    ("RHEVM-24208", ('atv_scsi_01.ks', DELL_PER515_01, 'create_vm_with_disk_check')),
    ("RHEVM-24114", ('atv_bvi_01.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24118", ('atv_bonda_02.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24120", ('atv_vlana_02.ks', DELL_PER515_01, 'create_new_host_check')),
    ("RHEVM-24119", ('atv_bva_02.ks', DELL_PER515_01, 'create_new_host_check')),
    # must install host before check
    ("RHEVM-invalid2", ('atv_fc_01.ks', DELL_PER510_01, 'create_new_host_check')),
    ("RHEVM-24174", ('atv_fc_01.ks', DELL_PER510_01, 'create_fc_sd_check')),
    ("RHEVM-24205", ('atv_fc_01.ks', DELL_PER510_01, 'create_vm_with_disk_check'))   
]
VDSM_TIER_TESTCASE_MAP = OrderedDict(t_cases)
