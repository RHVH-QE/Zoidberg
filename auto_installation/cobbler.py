import copy
import attr
import xmlrpclib
import logging

from .constants import CB_API, CB_CREDENTIAL


def _cb_cred_checker(instance, attribute, value):
    if not isinstance(value, tuple) and not isinstance(value, list):
        raise ValueError("credential must be `tuple` or `list`")
    elif len(value) != 2:
        raise ValueError("credential can only contain 2 elements")
    else:
        return True


@attr.s
class Cobbler(object):
    system_tpl = dict(
        name="",
        profile="",
        modify_interface={"macaddress-?": ""},
        comment="managed-by-zoidberg",
        status="testing",
        kernel_options="",
        kernel_options_post="")

    cb_api = attr.ib(default=CB_API)
    credential = attr.ib(default=CB_CREDENTIAL, validator=_cb_cred_checker)
    token = attr.ib(default=None)
    log = attr.ib(default=logging.getLogger("bender"))

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        self.log.warn("disconnected from {}".format(self.cb_api))

    @property
    def proxy(self):
        return xmlrpclib.Server(self.cb_api)

    @property
    def profiles(self):
        ret = self.proxy.get_profiles()
        return [pn['name'] for pn in ret if pn['name'].startswith('RHVH')]

    def login(self):
        self.token = self.proxy.login(*(self.credential))
        self.log.info("logging into {}, get token is {}".format(self.cb_api,
                                                                self.token))

    def find_system(self, name_pattern):
        self.log.info("start to querying system {}".format(name_pattern))

        ret = self.proxy.find_system(dict(name=name_pattern))
        if ret:
            self.log.info("found system : {}".format(ret))
            return True
        else:
            self.log.warning("system not exists")
            return False

    def add_new_system(self, **kwargs):
        system_id = self.proxy.new_system(self.token)
        params = copy.deepcopy(self.system_tpl)
        params.update(kwargs)

        self.log.info("add new host with {}".format(params))
        for k, v in params.items():
            self.proxy.modify_system(system_id, k, v, self.token)

        self.proxy.save_system(system_id, self.token)

    def remove_system(self, system_name):
        self.proxy.remove_system(system_name, self.token)


if __name__ == '__main__':
    # new_system = dict(
    #     name="dell-pet105-01",
    #     profile="RHVH-4.0-73-20170104.0",
    #     modify_interface={"macaddress-enp2s0": "00:22:19:27:54:c7"})

    # with Cobbler() as cb:
    #     cb.add_new_system(
    #         name="dell-pet105-01",
    #         profile="RHVH-4.0-73-20170104.0",
    #         modify_interface={"macaddress-enp2s0": "00:22:19:27:54:c7"})

    with Cobbler() as cb:
        print cb.profiles
