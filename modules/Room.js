// var Player = require('./Player').Player;
import {Player} from "./Player.js";
import {ServerSkull, ClientSkull} from "./Skull.js";
// import {ServerModule, ClientModule} from "./Module.js"
// var ServerModule = require('./Module').ServerModule;
// var ClientModule = require('./Module').ClientModule;

// class ServerRoom extends ServerModule {
class ServerRoom {
  constructor(io) {
    // super(io, "room", true);
    // this.io = io;
    this.io = io;
    this.ev = "room";
    this.playing = [];
    this.watching = [];
    this.game = undefined;

    this.io.on("connect", function(socket) {
      socket.on(this.ev, this.ioHandler.bind(this, socket));
      socket.emit(this.ev, "display", this.emitData());
      socket.on("disconnect", this.disconnectPlayer.bind(this, socket.id));
    }.bind(this));


    // this.nsp.on("connection", function(socket) {
    //   console.log("connected: ", socket.id)
    //   socket.on("name", this.setName.bind(this, socket));
    //   socket.on("play", this.ready.bind(this, socket.id))
    //   socket.on("kwalexadmin", startGame);
    //   this.nsp.to(`${socket.id}`).emit("display", this.emitData())
    // }.bind(this));
  }
  // registerSocket(socket) {
  //   // console.log("child")
  //   super.registerSocket(socket);
  //   socket.emit(this.ev, "display", this.emitData());
  // }
  ioHandler(socket, ...data) {
    var event = data[0];
    console.log("roomiohandler: ", event)
    if (event == "play") {
      this.ready(socket);
    }
    if (event == "name") {
      // console.log("calling name: ", data[1])
      this.setName(socket, data[1])
    }
    if (event == "kwalexadmin") {
      this.startGame(data[1])
      // this.io.emit(this.ev, "startGame", data[1])
      // this.io.emit()
    }
  }

  emitPlayer(player, ...data) {
    const socket = player.socket;
    if (socket) {
      // console.log("emitPlayer: ", data)
      // this.io.emit(...data);
      this.io.to(`${socket.id}`).emit(...data);
    } else {
      console.log("emitPlayer to bad socket")
    }
  }
  gameEmit(...data) {
    // console.log("gameEmit: ", data)
    this.io.emit(...data);
  }
  notifyMain(socket, str) {
    this.io.to(`${socket.id}`).emit(this.ev, "notifyMain", str);
  }
  notifySecondary(socket, str) {
    this.io.to(`${socket.id}`).emit(this.ev, "notifySecondary", str);
  }
  getSockets() {
    var ret = [];
    // var ids = [];
    for (var cp of this.playing) {
      ret.push(cp.socket);
      // if (cp.socket) ids.push(cp.socket.id);
    }
    // console.log("getSockets: ", ids);
    return ret;
  }
  getPlayerIndex(socket) {
    for (var i=0; i < this.playing.length; i++) {
      if (this.playing[i].socket && (this.playing[i].socket.id == socket.id)) return i;
    }
  }
  startGame(game) {
    if (game == "skull") this.game = new ServerSkull(this);
    if (this.game) {
      // this.game.emitData()
      for (var s of this.getSockets()) {
        if (s == undefined) continue;
        s.on(this.game.ev, this.gameHandler.bind(this, s));
        s.emit(this.ev, "startGame", game, ...this.game.initialData(s))
      }
      // this.io.emit(this.ev, "startGame", game, this.game.emitData());
      // this.io.emit(this.ev, "startGame", game, );

      this.game.start();
    }
  }
  endGame() {
    for (var s of this.getSockets()) {
      s.removeAllListeners(this.game.ev);
    }
    this.game = undefined;
    this.io.emit(this.ev, "endGame");
  }
  gameHandler(socket, ...data) {
    var i = this.getPlayerIndex(socket);
    if (i != undefined) {
      this.game.ioHandler(i, ...data);
    } else {
      console.log("bad index request")
    }
  }
  ready(socket) {
    const id = socket.id;
    for (var i = this.watching.length - 1; i >= 0; i--) {
      if (this.watching[i].socket.id == id) {
        if (this.game) {
          this.notifyMain(socket, "Wait for the current game to end.");
          return;
        } else {
          console.log("ready: ", id, this.watching.length)
          this.playing.push(this.watching[i])
          this.watching.splice(i,1)
        }
      }
    }
    for (var i = 0; i < this.playing.length; i++) {
      if (this.playing[i].socket && this.playing[i].socket.id == id && this.game) {
        this.io.to(`${id}`).emit(this.ev, "startGame", this.game.ev, ...this.game.initialData(this.playing[i].socket))
        socket.on(this.game.ev, this.gameHandler.bind(this, socket));
      }
    }
    this.emit()
  }
  setName(socket, name) {
    if (!name) return;
    var shouldAdd = true;
    var pWatching;
    var pPlaying;
    for (var cp of this.watching) {
      if (cp.name == name) {
        this.notifyMain(socket, "someone already got that one");
        shouldAdd = false;
        return;
      }
      if (cp.socket && cp.socket.id == socket.id) {
        pWatching = cp;
        shouldAdd = false;
        // cp.name = name.slice(0,8);
        // this.emit();
        // shouldAdd = false;
        // return;
      }

    }

    for (var cp of this.playing) {
      if (cp.socket && (cp.socket.id == socket.id)) {
        this.notifyMain(socket, "can't change it now");
        shouldAdd = false;
        return;
      }
      if (cp.name == name) {
        shouldAdd = false;
        if (cp.socket == undefined) {
          pPlaying = cp;
          // cp.socket = socket;
          // this.notifyMain(socket, "logging back in as: " + name)
        } else {
          this.notifyMain(socket, "name taken you idiots");
          return;
        }
      }
    }

    const nn = name.slice(0,8);
    if (!pWatching && !pPlaying) {
      this.watching.push(new Player(nn, socket));
      this.notifyMain(socket, "logged in as: " + nn);
      this.emit();
    } else if (pWatching && !pPlaying) {
      pWatching.name = nn;
      this.notifyMain(socket, "name changed to: " + nn);
      this.emit();
    } else if (!pWatching && pPlaying) {
      pPlaying.socket = socket;
      this.notifyMain(socket, "logging back in as: " + name);
    }
    // if (shouldAdd) {
    //   this.watching.push(new Player(name.slice(0,8), socket));
    //   this.emit()
    // }
  }
  // addPlayer(p) {
  //   var rejoined = false;
  //   for (var cp of this.playing) {
  //     if (cp.name == p.name) {
  //       cp.socket = p.socket
  //       rejoined = true;
  //       console.log("rejoined: ", p.name)
  //     }
  //   }
  //   if (!rejoined) {
  //     for (var cp of this.watching) {
  //       if (cp.name == )
  //     }
  //     this.watching.push(p)
  //   }
  //   this.emit()
  // }

  disconnectPlayer(id) {
    for (var cp of this.playing) {
      if (cp.socket != undefined && cp.socket.id == id) {
        cp.socket = undefined;
        console.log("disconnecting: ", id)
      }
    }

    for (var i = this.watching.length - 1; i >= 0; i--) {
      if (this.watching[i].socket.id == id) {
        console.log("removing: ", id, this.watching.length)
        this.watching.splice(i,1)
      }
    }
    this.emit()
  }

  emitData() {
    const pnames = [];
    for (var cp of this.playing) {
      pnames.push(cp.name)
    }
    const wnames = [];
    for (var cp of this.watching) {
      wnames.push(cp.name)
    }
    const output = {"playing":pnames, "watching":wnames};
    return output
  }
  emit() {
    this.io.emit(this.ev, "display", this.emitData())
    // this.nsp.emit("display", this.emitData())
  }


}


// class ClientRoom extends ClientModule {
class ClientRoom {
  constructor(socket, termMain, termRoom, termSide) {
    // super(socket, "room");
    this.socket = socket;
    this.ev = "room";
    this.termMain = termMain;
    this.termRoom = termRoom;
    this.termSide = termSide;
    // this.startGame = startGame;
    // this.socket = socket;

    // this.termMain.addCommand("room", "name", function(name) {
    //   this.emit("name", name);
    // }.bind(this));
    this.termMain.addCommand("room", "name", this.emit.bind(this, "name"));
    this.termMain.addCommand("room", "play", this.emit.bind(this, "play"));
    this.termMain.addCommand("room", "kwalexadmin", this.emit.bind(this, "kwalexadmin"));
    // this.termMain.addCommand("room", "timer", this.termMain.promptCountdown.bind(this.termMain, 3));
    // this.termMain.addCommand("room", "play", function() {
    //   this.emit("play");
    // }.bind(this));
    // this.termMain.addCommand("room", "kwalexadmin", function(game) {
    //   this.emit("kwalexadmin", game);
    // }.bind(this));
    // this.termRoom.addCommand("name", p => this.emit("name", p.args[0]));
    // this.termRoom.addCommand("play", p => this.emit("play"));


    this.socket.on(this.ev, this.ioHandler.bind(this, this.socket));
    this.activate();
    // this.socket.on("display", this.updateDisplay.bind(this));
    // this.socket.on("notification", function(m) {
    //   this.termMain.echo(m)
    // }.bind(this));
    // this.socket.on("startGame", this.startGame);
    // term.name = "Room"
    // term.settings().greetings = "Room"
  }
  emit(...data) {
    // console.log("emit: ", ...data);
    this.socket.emit(this.ev, ...data);
  }
  activate() {
    // this.termMain.push(this.termHandler.bind(this));
    // this.termMain.term.set_interpreter(this.termHandler.bind(this));
    this.termMain.mode = "room"
    this.termMain.term.set_prompt("Room> ");
    this.termMain.term.focus(true);
    this.termRoom.term.pause();
    this.termSide.term.pause();
  }
  deactivate() {
    this.socket.removeAllListeners(this.ev);
    // this.termMain.pop();
  }
  ioHandler(socket, ...data) {
    var event = data[0];
    console.log("roomiohandler: ", event, data)
    if (event == "notification") {
      this.termMain.echo(data[1]);
    }
    if (event == "display") {
      this.updateDisplay(data[1]);
    }
    if (event == "startGame") {
      this.startGame(...data);
    }
    if (event == "endGame") {
      this.game.deactivate();
      this.socket.removeAllListeners(this.game.ev);
      this.game = undefined;
      this.activate();
    }
    if (event == "endRound") {
      this.termMain.echo("New round starting: ");
      this.termMain.countdown(5);
    }
    if (event == "notifyMain") {
      this.termMain.echo(data[1])
    }
    if (event == "notifySecondary") {
      this.termNote.echo(data[1])
    }
  }
  startGame(ev, game, ...data) {
    // this.deactivate();
    if (game == "skull") this.game = new ClientSkull(this.socket, this.termMain, this.termSide, ...data);
    // this.deactivate();
    // this.game.updateDisplay(emitData)
    this.socket.on(this.game.ev, this.game.ioHandler.bind(this.game))
  }

  // termHandler(command, term) {
  //   // console.log("termHandler: ", command)
  //   var p = term.__T__.parse_command(command)
  //   // console.log(p)
  //   if (p.name == "name") {
  //     this.socket.emit(this.ev, "name", p.args[0])
  //   } else if (p.name == "play") {
  //     this.socket.emit(this.ev, "play")
  //   } else if (p.name == "kwalexadmin") {
  //     this.socket.emit(this.ev, p.name, p.args[0])
  //   } else if (p.name == "timer") {
  //     this.termMain.countdown(3);
  //   }
  //   // term.echo("handler",command)
  //   // this.term.echo("more")
  // }
  updateDisplay(data) {
    // console.log(data)
    this.termRoom.term.clear()
    this.termRoom.echo("Waiting: " + data.watching.join(", "));
    this.termRoom.echo("Playing: " + data.playing.join(", "));
  }

}




export { ServerRoom, ClientRoom };
// module.exports.ServerRoom = ServerRoom
