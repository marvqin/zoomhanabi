// import {ServerModule, ClientModule} from "./Module.js"

class Round {
  constructor(players, startingIndex, available, isAlive) {
    this.players = players;
    this.phase = "initial";
    this.cards = [];
    this.bids = [];
    this.status = [];
    this.cpIndex = startingIndex;
    this.n = this.players.length;
    this.cBid = 0;
    this.nCards = 0;
    this.guessIndex = [];
    this.available = available
    this.isAlive = isAlive;
    this.correctGuesses = 0;

    for (var cp of this.players) {
      this.cards.push([]);
      this.status.push(true);
      this.bids.push(0);
      this.guessIndex.push(-2)
    }

  }
  allHavePlayed() {
    if (this.phase != "initial") console.log("bad allHavePlayed()");
    for (var i=0; i < this.n; i++) {
      if (this.isAlive[i] && this.cards[i].length == 0) return false;
    }
    return true;
  }
  isCurrentPlayer(i) {
    return (i == this.cpIndex);
  }
  findPlayerIndex(name) {
    for (var i=0; i < this.n; i++) {
      if (this.players[i].name == name) {
        return i
      }
    }
  }

}

// class ServerSkull extends ServerModule{
class ServerSkull {
  constructor(room) {
    // super(io, "skull");
    this.ev = "skull";
    this.room = room
    this.players = room.playing;
    this.n = this.players.length;
    this.round = undefined;
    this.hands = [];
    this.points = [];
    this.isAlive = [];
    // this.onEnd = onEnd;

    for (var cp of this.players) {
      this.hands.push(["skull", "rose", "rose", "rose"]);
      this.points.push(0);
      this.isAlive.push(true);
    }
    // this.nsp.on("connection", function(socket) {
    //   console.log("connectedskull: ", socket.id)
    //   // socket.on("name", this.setName.bind(this, socket));
    //   // socket.on("play", this.ready.bind(this, socket.id))
    //   // socket.on("kwalexadmin", startGame);
    //   socket.on("play", function(card) {
    //     console.log("play", card);
    //     const i = this.getIndex(socket);
    //     this.play(i, card);
    //   }.bind(this));
    //   socket.on("bid", function(n) {
    //     const i = this.getIndex(socket);
    //     this.bid(i, Number(n));
    //   }.bind(this));
    //   this.nsp.to(`${socket.id}`).emit("display", this.emitData())
    // }.bind(this));
    this.startRound(0);
  }
  getSocket(i) {
    return this.players[i].socket;
  }
  getIndex(socket) {
    for (var i=0; i < this.players.length; i++) {
      if (this.players[i].socket.id == socket.id) return i;
    }
  }
  ioHandler(i, ...data) {
    console.log("skullioHandler", i, data)
    // var i = this.getIndex(socket);
    if (i != undefined) {
      var ev = data[0];
      // console.log("ioHandler: ", ev)
      if (ev == "play") {
        this.play(i, data[1]);
      }
      if (ev == "bid") {
        this.bid(i, Number(data[1]))
      }
      if (ev == "fold") {
        this.fold(i)
      }
      if (ev == "guess") {
        this.guess(i, data[1])
      }
      if (ev == "requestDisplay") {
        socket.emit("display", this.emitData())
      }
    }
  }
  start() {
    this.informInitial();
    // this.startRound(0);
  }
  startRound(sp) {
    // var pl = [];
    var availables = [];
    for (var i=0; i < this.n; i++) {
      availables.push(this.hands[i].slice())
    }
    // for (var i=0; i < this.n; i++) {
    //   if (this.isAlive[i]) {
    //     pl.push(this.players[i])
    //     availables.push(this.hands[i].slice())
    //   }
    // }
    this.round = new Round(this.players, sp, availables, this.isAlive);
    this.emit();
    this.informInitial();
  }
  canPlay(i, card) {
    console.log(i)
    if (!this.round.available[i].includes(card)) {
      return false;
    }
    if (this.round.phase == "initial" && this.round.cards[i].length == 0) {
      return true;
    }
    if (this.round.phase == "turns") {
      return this.round.isCurrentPlayer(i);
    }
    if (this.round.phase == "bidding") {
      return false;
    }
  }
  play(i, card) {
    if (this.canPlay(i, card)) {
      console.log("playing: ", i, card)
      this.round.cards[i].push(card);
      this.round.available[i].splice(this.round.available[i].indexOf(card), 1);
      this.round.nCards += 1;
      if (this.round.phase == "turns") {
        this.nextPlayer();
      }
      if (this.round.phase == "initial" && this.round.allHavePlayed()) {
        this.round.phase = "turns";
        this.informTurn();
      }
      this.emit();
    } else {
    this.room.notifyMain(this.getSocket(i), "cut the crap");
    }

  }
  canBid(i, amount) {
    console.log("canBid: ", i, amount);
    if (isNaN(amount) || amount < 0 || amount > this.round.nCards) {
      return false;
    }
    if (this.round.phase == "initial") {
      return false;
    }
    if (this.round.phase == "turns") {
      return this.round.isCurrentPlayer(i)
    }
    if (this.round.phase == "bidding") {
      return (this.round.isCurrentPlayer(i) && amount > this.round.cBid);
    }
  }
  bid(i, amount) {
    if (this.canBid(i, amount)) {
      this.round.bids[i] = amount;
      this.round.cBid = amount;
      this.round.phase = "bidding";
      this.nextPlayer();
      this.emit();
    } else {
      console.log("bad bid")
    }
  }
  canFold(i) {
    if (!this.round.isCurrentPlayer(i)) this.room.notifyMain(getSocket(i), "not your turn fool");
    return (this.round.isCurrentPlayer(i) && this.round.phase == "bidding");
  }
  fold(i) {
    if (this.canFold(i)) {
      this.round.status[i] = false;
      this.nextPlayer();
      this.emit();
    }
  }
  canGuess(i) {
    if (this.round.phase != "guessing") {
      return false;
    }
    return this.round.isCurrentPlayer(i);
  }
  guess(i, name) {
    // console.log("guess: ",i,name);
    if (this.canGuess(i)) {
      var index = this.round.findPlayerIndex(name);
      // console.log("guessindex: ", index)
      if (index != undefined) {
        var gi = this.round.guessIndex[index]
        // console.log("guess: ", gi);
        if (gi >= 0) {
          var outcome = this.round.cards[index][gi];
          this.round.guessIndex[index] -= 1;
          // console.log("guessoutcome: ", outcome)
          if (outcome == "skull") {
            this.endRound(i, false, index);
          }
          if (outcome == "rose") {
            this.round.correctGuesses += 1;
            if (this.round.correctGuesses == this.round.cBid) {
              this.endRound(i, true);
            }
          }
          this.emit();
        }
      }
    }
  }
  nextPlayer() {
    if (this.round.phase == "initial") return;
    var origIndex = this.round.cpIndex;
    for (var i=0; i < this.n; i++) {
      this.round.cpIndex += 1;
      if (this.round.cpIndex == this.n) {
        this.round.cpIndex = 0;
      }
      const cpi = this.round.cpIndex;
      if (this.round.isAlive[cpi] && this.round.status[cpi]) {
        break;
      }
    }
    if (this.round.phase == "bidding") {
      const cpi = this.round.cpIndex;
      if (this.round.bids[cpi] == this.round.cBid || origIndex == cpi) {
        this.guessPhase();
      }
    }
    this.informTurn();

  }
  informInitial() {
    for (var cp of this.players) {
      this.informTurn(cp);
    }
  }
  informTurn(p) {
    var pl;
    if (p != undefined) pl = p;
    else pl = this.players[this.round.cpIndex];
    const index = this.round.findPlayerIndex(pl.name);
    const available = this.round.available[index];
    const cards = this.round.cards[index];
    if (this.round.phase == "turns") {
      this.room.emitPlayer(pl, this.ev, "yourTurn", cards, available)
    } else if (this.round.phase == "initial") {
      this.room.emitPlayer(pl, this.ev, "initialPhase", cards, available)
    }
  }
  guessPhase() {
    this.round.phase = "guessing";
    this.round.guessIndex = [];
    for (var cArray of this.round.cards) {
      this.round.guessIndex.push(cArray.length - 1);
    }

    var cp = this.round.cpIndex;
    for (var i=0; i < this.round.cards[cp].length; i++) {
      this.guess(cp, this.round.players[cp].name);
    }

  }
  endRound(i, outcome, sp) {
    console.log("endRound: ",i,outcome);
    this.room.gameEmit(this.ev, "endRound");
    if (outcome) {
      this.points[i] += 1;
      if (this.points[i] == 2) {
        this.endGame(i);
      }
      setTimeout(this.startRound.bind(this, i), 6000);
      // this.startRound(i);
    }
    if (!outcome) {
      const r = Math.floor(Math.random() * this.hands[i].length);
      this.hands[i].splice(r, 1);
      if (this.hands[i].length == 0) {
        this.isAlive[i] = false;
      }
      setTimeout(this.startRound.bind(this, sp), 6000);
      // this.startRound(sp);
    }

  }
  endGame(winnerIndex) {
    // const pl = this.round.getPlayerIndex(winnerIndex);
    this.emit();
    this.room.endGame();
  }
  publicStrings() {
    var ret = [];
    for (var i=0; i < this.n; i++) {
      var iArray = [];
      for (var j=0; j < this.round.cards[i].length; j++) {
        var s = this.round.cards[i][j];
        var c;
        if (s == "rose") c = "R";
        if (s == "skull") c = "S";
        const gi = this.round.guessIndex[i];
        if (gi == -2 || gi >= j) c = "C";
        iArray.push(c)
      }
      ret.push(iArray.join(""));
    }
    return ret;
  }
  emitData() {
    var pNames = [];
    for (var cp of this.players) {
      pNames.push(cp.name)
    }

    var roundNames = [];
    for (var cp of this.round.players) {
      roundNames.push(cp.name)
    }
    const hLengths = [];
    for (var i=0; i < this.players.length; i++) {
      hLengths.push(this.hands[i].length)
    }
    var r = this.round;
    var ret = {}
    ret["pN"] = pNames;
    ret["pts"] = this.points;
    // ret["av"] = this.available;
    // ret["rN"] = roundNames;
    ret["phase"] = r.phase;
    ret["cp"] = r.cpIndex;
    ret["status"] = r.status;
    ret["pStrs"] = this.publicStrings();
    // ret["cards"] = r.cards;
    ret["bids"] = r.bids;
    ret["cBid"] = r.cBid;
    ret["nCards"] = r.nCards;
    ret["guessIndex"] = r.guessIndex;
    ret["cg"] = r.correctGuesses;
    ret["hLengths"] = hLengths;
    // ret["hands"] = this.hands;
    // ret = [pNames, this.points, this.available, roundNames, r.phase, r.cpIndex, r.status, r.cards, r.bids, r.cBid, r.nCards, r.guessIndex]
    return ret;
  }
  emit() {
    this.room.gameEmit(this.ev, "display", this.emitData());
    // this.io.emit(this.ev, "display", this.emitData())
  }
}

// class ClientSkull extends ClientModule {
class ClientSkull {
  constructor(socket, termMain, termSide) {
    // super(io, "skull");
    this.socket = socket;
    this.ev = "skull";
    this.termMain = termMain;
    this.termSide = termSide;
    // this.socket.on("display", this.updateDisplay.bind(this));
    this.activate();
    // console.log("skull active", termMain)
    // this.requestDisplay();
  }
  ioHandler(...data) {
    var ev = data[0];
    console.log("skullioHandler: ", ev)

    if (ev == "yourTurn") {
      this.termMain.echo("Your turn. played: " + JSON.stringify(data[1]) + " , available: " + JSON.stringify(data[2]));
    }
    if (ev == "initialPhase") {
      this.termMain.echo("Initial phase, play a card. available: " + JSON.stringify(data[2]));
    }
    if (ev == "display") {
      this.updateDisplay(data[1]);
    }
    if (ev == "yourGuess") {
      this.termMain.echo("Your turn to guess.");
    }
    if (ev == "endRound") {
      this.termMain.term.clear();
      this.termSide.countdown(5);
    }

  }
  // requestDisplay() {
  //   this.socket.emit(this.eventName, "requestDisplay");
  // }
  activate() {
    // super.activate();
    // this.termMain.push(this.termHandler.bind(this));
    this.termMain.term.set_interpreter(this.termHandler.bind(this));
    this.termMain.term.set_prompt("skull> ");
  }
  deactivate() {
    // this.termMain.pop();
  }
  termHandler(command, term) {
    const sc = command.slice(0, 256);
    console.log("clientskulltermHandler: ", sc)
    var p = term.__T__.parse_command(sc)
    // console.log(p)
    const c = p.name;
    if (c == "rose" || c == "r") {
      this.socket.emit(this.ev, "play", "rose");
    } else if (c == "skull" || c == "s") {
      this.socket.emit(this.ev, "play", "skull");
    } else if (c == "bid") {
      this.socket.emit(this.ev, "bid", p.args[0]);
    } else if (c == "fold") {
      this.socket.emit(this.ev, "fold");
    } else if (c == "guess") {
      this.socket.emit(this.ev, "guess", p.args[0]);
    } else {
      term.echo("bad command");
    }
    // term.echo("handler",command)
    // this.term.echo("more")
  }
  updateDisplay(d) {
    console.log(d)
    var rt = this.termSide.term;
    rt.clear();
    // const s1 = `Phase: ${d["phase"]}, cBid: ${d["cBid"]}, cP: ${d["cp"]}, `;
    // rt.echo(s1);
    rt.echo(`Phase: ${d["phase"]}`);
    rt.echo(`nCards: ${d["nCards"]}`);
    rt.echo(`cBid: ${d["cBid"]}`);
    rt.echo(`cP: ${d["cp"]}`);
    rt.echo(`${d["cg"]}/${d["cBid"]} guesses`);
    rt.echo("\n");
    const pNames = d["pN"];
    for (var i=0; i < pNames.length; i++) {
      var isTurn;
      if (d["cp"] == i) isTurn = "*";
      else isTurn = " ";
      var s = isTurn + pNames[i].padStart(8, " ") + ": " + d["pStrs"][i];
      // var s = isTurn + pNames[i].padStart(8, " ") + ": " + "C".repeat(d["cards"][i].length);
      if (d["bids"][i] != 0 && d["status"][i]) {s += d["bids"][i];}
      else if (!d["status"][i]) {s += "-";}
      rt.echo(s);
    }
    rt.echo("\n\n********\n\n");
    for (var i=0; i < pNames.length; i++) {
      var s = pNames[i].padStart(9, " ") + ": " + `${d["hLengths"][i]} cards, ${d["pts"][i]} points`;
      rt.echo(s);
    }
    rt.echo(".")
    // rt.echo(d["phase"]);
    // rt.echo(d["cBid"]);
  }
}

export {ServerSkull, ClientSkull}
