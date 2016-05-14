from auto_installation.beaker import BeakerProvision


def release_system():
    bk = BeakerProvision()
    r = bk.release('dell-per510-01.lab.eng.pek2.redhat.com')
    assert r == 0
