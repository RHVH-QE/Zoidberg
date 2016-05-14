from auto_installation.beaker import BeakerProvision

from auto_installation.utils import ReserveUserWrongException

if __name__ == '__main__':
    bkr = BeakerProvision(srv_ip='10.66.9.216', srv_port='5000')
    bkr.provision(bkr_name='dell-per515-01.lab.eng.pek2.redhat.com')

