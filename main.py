from auto_installation import app, setup_funcs, rd_conn, socketio

if __name__ == '__main__':
    setup_funcs(rd_conn)
    # app.run('0.0.0.0', debug=True)
    socketio.run(app, '0.0.0.0', debug=False)
