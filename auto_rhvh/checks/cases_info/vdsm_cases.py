from common import DELL_PET105_01, DELL_PER510_01, DELL_PER515_01

VDSM_TIER_TESTCASE_MAP = {  # sequential cases for each scenario
    "RHEVM-18113": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18114": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl1_create_local_sd_check'),
    "RHEVM-18197": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl2_include_rhgs_pkg_check'),
    "RHEVM-18136": ('atv_local-vlani_01.ks', DELL_PER515_01, 'cl3_fcoe_service_check'),
    "RHEVM-18118": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18135": ('atv_local-vlani_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18117": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18137": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18120": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cn1_create_nfs_sd_check'),
    "RHEVM-18128": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cn2_create_iso_sd_check'),
    "RHEVM-18121": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv1_create_vm_with_disk_check'),
    "RHEVM-18122": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv3_vm_life_cycle_check'),
    "RHEVM-18130": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cv9_delete_vm_check'),
    "RHEVM-18123": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cz1_maintenance_host_check'),
    "RHEVM-18127": ('atv_nfs-bondi_02.ks', DELL_PER515_01, 'cz2_remove_host_check'),
    # must install host before check
    "RHEVM-invalid1": ('atv_scsi_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18115": ('atv_scsi_01.ks', DELL_PER515_01, 'cs1_create_scsi_sd_check'),
    "RHEVM-18132": ('atv_scsi_01.ks', DELL_PER515_01, 'cv1_create_vm_with_disk_check'),
    "RHEVM-18134": ('atv_scsi_01.ks', DELL_PER515_01, 'cv2_attach_second_disk_to_vm_check'),
    "RHEVM-18119": ('atv_bvi_01.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18156": ('atv_bonda_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18160": ('atv_vlana_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    "RHEVM-18157": ('atv_bva_02.ks', DELL_PER515_01, 'ca0_create_new_host_check'),
    # must install host before check
    "RHEVM-invalid2": ('atv_fc_01.ks', DELL_PER510_01, 'ca0_create_new_host_check'),
    "RHEVM-18116": ('atv_fc_01.ks', DELL_PER510_01, 'cf1_create_fc_sd_check'),
    "RHEVM-18131": ('atv_fc_01.ks', DELL_PER510_01, 'cv1_create_vm_with_disk_check'),
    "RHEVM-18133": ('atv_fc_01.ks', DELL_PER510_01, 'cv2_attach_second_disk_to_vm_check'),
}
