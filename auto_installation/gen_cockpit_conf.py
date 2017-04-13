import json
import attr
import tempfile


@attr.s
class CockpitConf(object):
    ip = attr.ib()
    build = attr.ib()
    profiles = attr.ib()

    def gen_json(self):
        conf = dict()
        conf['host_ip'] = self.ip
        conf['test_profile'] = self.profiles
        conf['test_build'] = self.build

        cfg = tempfile.mktemp(suffix="cockpit")

        with open(cfg, 'w') as fp:
            json.dump(conf, fp)
        return cfg


if __name__ == '__main__':
    pass
