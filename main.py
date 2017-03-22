from auto_installation import app, setup_funcs, rd_conn
from gevent.pywsgi import WSGIServer

if __name__ == '__main__':
    setup_funcs(rd_conn)
    srv = WSGIServer(('', 5000), app)
    srv.serve_forever()
