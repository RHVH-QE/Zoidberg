import attr
from pymongo import MongoClient
from urllib import quote_plus


@attr.s
class MongoQuery(object):
    user = attr.ib(default='meteor')
    password = attr.ib(default='redhat')
    host = attr.ib(default='10.66.148.42:27017/meteordb')
    db_name = attr.ib(default='meteordb')

    @property
    def uri(self):
        return "mongodb://%s:%s@%s" % (quote_plus(self.user),
                                       quote_plus(self.password), self.host)

    @property
    def db(self):
        return MongoClient(self.uri)[self.db_name]

    def collection(self, name):
        return self.db[name]

    def rhvh_build_names(self, q='4.1'):
        c = self.collection('resources.rhevh36ngn')
        query = 'redhat-virtualization-host-{}'.format(q)
        return [
            i['build_name'] for i in c.find()
            if i['build_name'].startswith(query)
        ]

    def machines(self, q=''):
        c = self.collection('machines')
        # for i in c.find(projection=['basic.ids.hostname', 'comments']):
        #     print i.get('comments', [''])
        auto = [
            i['basic']['ids']['hostname']
            for i in c.find(projection=['basic.ids.hostname', 'comments'])
            if i['basic']['ids'] and i.get('comments', [''])[0] == 'zoidberg'
        ]
        manual = [
            i['basic']['ids']['hostname']
            for i in c.find(projection=['basic.ids.hostname', 'comments'])
            if i['basic']['ids'] and i.get('comments', [''])[0] != 'zoidberg'
        ]
        return [auto, manual]


if __name__ == '__main__':
    print MongoQuery().machines()
