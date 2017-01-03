import xmlrpclib
from constants import CB_CREDENTIAL, CB_PROFILE


class Cobbler(object):
    """A simple wrapper around Cobbler's XMLRPC API.

    Cobbler also provides it's own python bindings but those are just
    distributed with all the other stuff. This small wrapper can be used
    as long as the bindigs are not split from the rest.
    """
    server_url = None
    server = None
    ssh_uri = None
    token = None

    #        "http://cobbler-server.example.org/cobbler_api"
    def __init__(self, server_url):
        self.server_url = server_url
        self.server = xmlrpclib.Server(server_url)
        self.args = {'kernel_options': ""}

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        pass

    def login(self):
        self.token = self.server.login(*(CB_CREDENTIAL))
        return self

    def sync(self):
        print("Syncing")
        self.server.sync(self.token)

    def assign_defaults(self, system_handle, profile, additional_args):
        args = {
            "profile": profile,
            "comment": "managed-by-zoidberg",
            "status": "testing",
            "kernel_options": "",
            "kernel_options_post": ""
        }

        if additional_args is not None:
            print("Adding additional args: %s" % additional_args)
            args.update(additional_args)

        self.modify_system(system_handle, args)

    def new_system(self):
        """Add a new system.
        """
        print("Adding a new system")
        return self.server.new_system(self.token)

    def get_system_handle(self, name):
        return self.server.get_system_handle(name, self.token)

    def modify_system(self, system_handle, args):
        for k, v in args.items():
            print("Modifying system: %s=%s" % (k, v))
            self.server.modify_system(system_handle, k, v, self.token)
        self.server.save_system(system_handle, self.token)

    def get_profile_handle(self, name):
        return self.server.get_profile_handle(name, self.token)

    def modify_profile(self, profile_handle, args):
        for k, v in args.items():
            print("Modifying profile: %s=%s" % (k, v))
            self.server.modify_profile(profile_handle, k, v, self.token)
        self.server.save_profile(profile_handle, self.token)

    def set_netboot_enable(self, name, pxe):
        """(Un-)Set netboot.
        """
        args = {"netboot-enabled": 1 if pxe else 0}

        system_handle = self.get_system_handle(name)
        self.modify_system(system_handle, args)

    def remove_system(self, name):
        try:
            self.server.remove_system(name, self.token)
        except Exception as e:
            print("Exception while removing host: %s" % e.message)
            print("name: %s, token: %s" % (name, self.token))

    def profiles(self):
        return [
            e["name"] for e in self.server.get_profiles(self.token, 1, 1000)
        ]

    def profile(self, name):
        return self.server.get_blended_data(name, "")

    def systems(self):
        return [
            e["name"] for e in self.server.get_systems(self.token, 1, 1000)
        ]

    def system(self, name):
        return self.server.get_system(name, True)
        # Both have problems with None profiles:

    #        return self.server.get_system_as_rendered(name)
    #        return self.server.get_blended_data("", name)

    def power_system(self, name, power):
        assert power in ["on", "off", "status", "reboot"]
        print("Setting power '%s' on '%s'" % (power, name))
        args = {"power": power, "systems": [name]}
        return self.server.background_power_system(args, self.token)

    def change_system(self, bkr_name, args):
        sh = self.get_system_handle(bkr_name)
        self.assign_defaults(sh, CB_PROFILE, args)
        self.set_netboot_enable(bkr_name, True)


if __name__ == '__main__':
    pass
