from Skull import ServerSkull
import eventlet

class Player:
    def __init__(self, name, sid):
        self.name = name
        self.sid = sid
        self.connected = True


class Room:
    def __init__(self, sio):
        self.sio = sio
        self.ev = "room";
        self.playing = [];
        self.watching = [];
        self.game = None;
        sio.on('connect', self.on_connect)
        sio.on('disconnect', self.on_disconnect)
        sio.on('message', self.io_handler)


    def on_connect(self, sid, environ):
        print('connect ', sid)
        self.sio.emit(self.ev, ("display", self.get_emit_data()), room=sid);
        print("emit data sent")

    def on_disconnect(self, sid):
        print('disconnect ', sid)
        for pp in self.playing:
            if pp.sid == sid:
                pp.connected = False

        for i in reversed(range(len(self.watching))):
            if self.watching[i].sid == sid:
                self.watching.pop(i)

    def io_handler(self, sid, data):
        print("room::io_handler: ", data)
        if "room" in data:
            rd = data["room"]
            if "name" in rd:
                self.set_name(sid, rd["name"])
                return
            if rd == "play":
                self.ready(sid)
                return
            if "kwalexadmin" in rd:
                self.start_game(rd["kwalexadmin"])
            if "ping" in rd:
                self.notify_main(sid, "pong")
            if rd == "watch":
                self.watch(sid)
        elif self.game_ev in data:
            self.game.io_handler(sid, data)
                # eventlet.spawn_after(3, self.notify_main, sid, "pong2")

    def set_name(self, sid, longname):
        name = longname[0:8]
        # print("set name: ", name)

        # watching_names = [cp.name for cp in self.watching]
        # watching_sockets = [cp.sid for cp in self.watching]
        # playing_names = [cp.name for cp in self.playing]
        # playing_sockets = [cp.sid for cp in self.playing]
        #
        # match_watching = [cp for cp in self.watching if cp.sid == sid]
        # match_playing = [cp for cp in self.playing if cp.sid == sid]

        mws = [cp for cp in self.watching if cp.sid == sid]
        mps = [cp for cp in self.playing if cp.sid == sid]
        mwn = [cp for cp in self.watching if cp.name == name]
        mpn = [cp for cp in self.playing if cp.name == name]

        matched_watcher = mws[0] if len(mws) > 0 else None
        matched_player = mps[0] if len(mps) > 0 else None


        if len(mwn) > 0:
            self.notify_main(sid, "someone already got that one")
            return

        if matched_player:
            self.notify_main(sid, "can't change it now")
            return
        elif len(mpn) > 0:
            if mpn[0].connected == False:
                matched_player = mpn[0]
            else:
                self.notify_main(sid, "name taken you idiots")
                return

        if not matched_player and not matched_watcher:
            self.notify_main(sid, "logging in as: {}".format(name))
            self.watching.append(Player(name, sid))
        elif not matched_player and matched_watcher:
            self.notify_main(sid, "name changed to: {}".format(name))
            matched_watcher.name = name
        elif matched_player and not matched_watcher:
            matched_player.sid = sid
            matched_player.connected = True
            self.notify_main(sid, "logging back in as: {}".format(name))

        self.emit_display()


    def ready(self, sid):
        print("ready: ", sid)
        for i in reversed(range(len(self.watching))):
            if self.watching[i].sid == sid:
                if self.game:
                    self.notifyMain(sid, "Wait for the current game to end.")
                    return
                else:
                    # console.log("ready: ", id, self.watching.length)
                    self.playing.append(self.watching[i])
                    self.watching.pop(i)

        self.emit_display()

    def watch(self, sid):
        for i in reversed(range(len(self.playing))):
            if self.playing[i].sid == sid:
                cp = self.playing[i]
                self.playing.pop(i)
                self.watching.append(cp)
                self.emit_display()

    def start_game(self, gamename):
        if gamename == "skull":
            self.game_ev = gamename
            self.game = ServerSkull(self);
        if self.game:
            for cp in self.playing:
                iData = self.game.initialData(cp.sid)
                fData = ["startGame", gamename]
                fData.extend(iData)
                self.sio.emit(self.ev, tuple(fData), room=cp.sid)
        self.game.start()

    def end_game(self):
        self.game = None;
        self.sio.emit(self.ev, "endGame");

    def notify_main(self, sid, msg):
        self.sio.emit(self.ev, ("notifyMain", msg), room=sid)
        # print("notify_main: ", msg)

    def get_emit_data(self):
        output = {"playing":[cp.name for cp in self.playing],
                "watching":[cp.name for cp in self.watching]}
        return output

    def emit_display(self):
        self.sio.emit(self.ev, ("display", self.get_emit_data()))

    def emit_player(self, player, d):
        self.sio.emit(self.game_ev, d, room=player.sid)

    def emit_game(self, d):
        self.sio.emit(self.game_ev, d)
