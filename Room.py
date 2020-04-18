class Player:
    def __init__(self, name, sid):
        self.name = name
        self.sid = sid

class Room:
    def __init__(self, sio):
        self.sio = sio
        self.ev = "room";
        self.playing = [];
        self.watching = [];
        self.game = None;
        sio.on('connect', self.on_connect)
        sio.on('disconnect', self.on_disconnect)
        sio.on('room', self.io_handler)


    def on_connect(self, sid, environ):
        print('connect ', sid)
        self.sio.emit(self.ev, ("display", self.emit_data()));

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    def io_handler(self, data):
        print("io_handler: ", data)

    def emit_data(self):
        output = {"playing":[cp.name for cp in self.playing],
                "watching":[cp.name for cp in self.watching]}
        return output
