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
      console.log("calling name: ", data[1])
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
      for (var s of this.getSockets()) {
        if (s == undefined) continue;
        s.on(this.game.ev, this.gameHandler.bind(this, s));
      }
      this.io.emit(this.ev, "startGame", game, this.game.emitData());
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
    if (this.game) return;
    const id = socket.id;
    for (var i = this.watching.length - 1; i >= 0; i--) {
      if (this.watching[i].socket.id == id) {
        console.log("ready: ", id, this.watching.length)
        this.playing.push(this.watching[i])
        this.watching.splice(i,1)
      }
    }
    for (var i = 0; i < this.playing.length; i++) {
      if (this.playing[i].socket && this.playing[i].socket.id == id && this.game) {
        this.io.to(`${id}`).emit(this.ev, "startGame", this.game.ev, this.game.emitData())
        socket.on(this.game.ev, this.gameHandler.bind(this, socket));
      }
    }
    this.emit()
  }
  setName(socket, name) {
    if (!name) return;
    // console.log(socket.id)
    var shouldAdd = true;
    for (var cp of this.playing) {
      if (cp.socket && (cp.socket.id == socket.id)) {
        this.notifyMain(socket, "can't change it now");
        shouldAdd = false;
        return;
      }
      if (cp.name == name.slice(0,8)) {
        shouldAdd = false;
        if (cp.socket == undefined) {
          cp.socket = socket;
          shouldAdd = false;
          break;
        } else {
          this.notifyMain(socket, "name taken");
        }
        // } else if (cp.socket.id == socket.id) {
        //   // cp.name = name; // disallow name change during playing
        //   shouldAdd = false;
        // }
      }
    }

    for (var cp of this.watching) {
      if (cp.socket && cp.name == name) {
        this.notifyMain(socket, "name taken you idiots");
        shouldAdd = false;
        return;
      }
      if (cp.socket && cp.socket.id == socket.id) {
        cp.name = name;
        shouldAdd = false;
      }

    }

    if (shouldAdd) {
      this.watching.push(new Player(name.slice(0,8), socket));
    }
    this.emit()
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
    this.activate();
    this.socket.on(this.ev, this.ioHandler.bind(this, this.socket));
    // this.socket.on("display", this.updateDisplay.bind(this));
    // this.socket.on("notification", function(m) {
    //   this.termMain.echo(m)
    // }.bind(this));
    // this.socket.on("startGame", this.startGame);
    // term.name = "Room"
    // term.settings().greetings = "Room"
  }
  activate() {
    // this.termMain.push(this.termHandler.bind(this));
    this.termMain.set_interpreter(this.termHandler.bind(this));
    this.termMain.set_prompt("Room> ")
  }
  deactivate() {
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
      this.startGame(data[1], data[2]);
    }
    if (event == "endGame") {
      this.game.deactivate();
      this.socket.removeAllListeners(this.game.ev);
      this.game = undefined;
      this.activate();
    }
    if (event == "notifyMain") {
      this.termMain.echo(data[1])
    }
    if (event == "notifySecondary") {
      this.termNote.echo(data[1])
    }
  }
  startGame(game, emitData) {
    this.deactivate();
    if (game == "skull") this.game = new ClientSkull(this.socket, this.termMain, this.termSide);
    // this.deactivate();
    this.game.updateDisplay(emitData)
    this.socket.on(this.game.ev, this.game.ioHandler.bind(this.game))
  }
  // activate() {
  //   super.activate()
  //   this.termMain.push(this.termHandler.bind(this));
  // }
  // deactivate() {
  //   this.termMain.pop()
  // }
  termHandler(command, term) {
    // console.log("termHandler: ", command)
    var p = term.__T__.parse_command(command)
    // console.log(p)
    if (p.name == "name") {
      this.socket.emit(this.ev, "name", p.args[0])
    } else if (p.name == "play") {
      this.socket.emit(this.ev, "play")
    } else if (p.name == "kwalexadmin") {
      this.socket.emit(this.ev, p.name, p.args[0])
    }
    // term.echo("handler",command)
    // this.term.echo("more")
  }
  updateDisplay(data) {
    // console.log(data)
    this.termRoom.clear()
    this.termRoom.echo("Waiting: " + data.watching.join(", "));
    this.termRoom.echo("Playing: " + data.playing.join(", "));
  }

}




export { ServerRoom, ClientRoom };
// module.exports.ServerRoom = ServerRoom
