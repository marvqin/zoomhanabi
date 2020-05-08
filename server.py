import eventlet
import socketio
from Room import Room

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    # '/': {'content_type': 'text/html', 'filename': 'index.html'},
    '/': 'index.html',
    '/modules': 'modules'
})

# @sio.event
# def connect(sid, environ):
#     print('connect ', sid)
#
# @sio.event
# def my_message(sid, data):
#     print('message ', data)
#
# @sio.event
# def disconnect(sid):
#     print('disconnect ', sid)

if __name__ == '__main__':
    r = Room(sio)
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 3000)), app)
