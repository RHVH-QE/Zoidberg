from auto_installation import app, setup_funcs, RD_CONN

if __name__ == '__main__':
    setup_funcs(RD_CONN)
    app.run('0.0.0.0', debug=True)
