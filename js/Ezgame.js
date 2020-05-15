class Ezgame {
  constructor(socket, termMain, termSide, name, pIndex, dispData) {
    // super(io, "skull");
    this.socket = socket;
    this.ev = "ezgame";
    this.termMain = termMain;
    this.termSide = termSide;

    this.termMain.addCommand(this.ev, ["choose", "c"], c => this.emit({choose:c}));
    // this.termMain.addCommand("skull", ["rose", "r"], () => this.emit("rose"));
    // this.termMain.addCommand("skull", ["skull", "s"], () => this.emit("skull"));
    //
    // this.termMain.addCommand("skull", ["bid", "b"], (b) => this.emit({bid:b}));
    // this.termMain.addCommand("skull", ["fold", "f"], () => this.emit("fold"));
    // this.termMain.addCommand("skull", ["guess", "g"], (g) => this.emit({guess:g}));
    this.activate();

    this.name = name;
    this.pIndex = pIndex;
    if (pIndex != undefined) {
      this.isPlaying = true;
    } else {
      this.isPlaying = false;
    }
    this.updateDisplay(dispData);
    // console.log("skull active", termMain)
    // this.requestDisplay();
  }
  ioHandler(...data) {
    var ev = data[0];
    console.log("ezgame handler: ", ev)

    if (ev == "yourTurn") {
      this.termMain.echo("Your turn. played: " + JSON.stringify(data[1]) + " , available: " + JSON.stringify(data[2]));
      // this.termMain.promptCountdown(24)
    }
    if (ev == "initialPhase") {
      this.termMain.term.clear();
      this.termMain.echo("Initial phase, play a card. available: " + JSON.stringify(data[2]));
      // this.termMain.promptCountdown(24)
    }
    if (ev == "display") {
      console.log(data[1])
      this.updateDisplay(data[1]);
    }
    // if (ev == "yourGuess") {
    //   this.termMain.echo("Your turn to guess.");
    // }
    if (ev == "endRound") {
      // this.termMain.term.clear();
      this.termMain.echo("Round over.")
      this.termSide.countdown(5);
    }
    if (ev == "notifyMain") {
      this.termMain.echo(data[1]);
    }
    // if (ev == "initialData") {
    //   console.log("initialData: ", data)
    //   this.name = data[1]
    //   this.pIndex = data[2]
    //   this.updateDisplay(data[3])
    //   console.log("initial data", this)
    // }

  }
  // requestDisplay() {
  //   this.socket.emit(this.eventName, "requestDisplay");
  // }
  emit(d) {
    console.log("emit: ", d)
    this.socket.emit("message", {[this.ev]:d});
  }
  activate() {
    // super.activate();
    // this.termMain.push(this.termHandler.bind(this));
    // this.termMain.term.set_interpreter(this.termHandler.bind(this));
    // this.termMain.term.set_prompt("skull> ");
    console.log("ezgame activate")
    this.termMain.mode = this.ev
    this.termMain.term.set_prompt(this.ev +"> ");
  }
  deactivate() {
    // this.termMain.pop();
  }
  // termHandler(command, term) {
  //   const sc = command.slice(0, 256);
  //   console.log("clientskulltermHandler: ", sc)
  //   var p = term.__T__.parse_command(sc)
  //   // console.log(p)
  //   const c = p.name;
  //   if (c == "rose" || c == "r") {
  //     this.socket.emit(this.ev, "play", "rose");
  //   } else if (c == "skull" || c == "s") {
  //     this.socket.emit(this.ev, "play", "skull");
  //   } else if (c == "bid") {
  //     this.socket.emit(this.ev, "bid", p.args[0]);
  //   } else if (c == "fold") {
  //     this.socket.emit(this.ev, "fold");
  //   } else if (c == "guess") {
  //     this.socket.emit(this.ev, "guess", p.args[0]);
  //   } else {
  //     term.echo("bad command");
  //   }

    // term.echo("handler",command)
    // this.term.echo("more")
  //}
  updateDisplay(d) {
    var rt = this.termSide.term;
    rt.clear();
    // rt.echo(`Phase: ${d["phase"]}`);
    // rt.echo(`nCards: ${d["nCards"]}`);
    // rt.echo(`cBid: ${d["cBid"]}`);
    // rt.echo(`cP: ${d["cp"]}`);
    // rt.echo(`${d["cg"]}/${d["cBid"]} guesses`);
    // rt.echo("\n");
    const pNames = d["pN"];
    for (var i=0; i < pNames.length; i++) {
      // var isTurn;
      // if (d["cp"] == i) isTurn = "*";
      // else isTurn = " ";
      var s = pNames[i].padStart(8, " ") + ": " + d["history_strings"][i] + d["public_choices"][i];
      // var s = isTurn + pNames[i].padStart(8, " ") + ": " + "C".repeat(d["cards"][i].length);
      // if (d["bids"][i] != 0 && d["status"][i]) {s += d["bids"][i];}
      // else if (!d["status"][i]) {s += "-";}
      rt.echo(s);
    }
    rt.echo("\n\n*******Score*******\n\n");
    for (var i=0; i < pNames.length; i++) {
      // var isTurn;
      // if (d["cp"] == i) isTurn = "*";
      // else isTurn = " ";
      var s = pNames[i].padStart(8, " ") + ": " + d["points"][i];
      // var s = isTurn + pNames[i].padStart(8, " ") + ": " + "C".repeat(d["cards"][i].length);
      // if (d["bids"][i] != 0 && d["status"][i]) {s += d["bids"][i];}
      // else if (!d["status"][i]) {s += "-";}
      rt.echo(s);
    }
    if (d["is_over"] == false) {
      const t = Math.round((d["scT"] - Date.now())/1000) - 1;
      this.termMain.promptCountdown(t)
    } else {
      this.termMain.endPromptCountdown()
    }
    // rt.echo(d["phase"]);
    // rt.echo(d["cBid"]);
    // if (d["phase"] != "ended") {
    //   var havePlayed;
    //   if (this.isPlaying) {
    //     havePlayed = d["pStrs"][this.pIndex].includes("C")
    //   }
    //   // console.log("havePlayed: ", havePlayed)
    //   if (this.isPlaying && ((d["phase"] == "initial" && !havePlayed) || (d["phase"] != "initial" && d["cp"] == this.pIndex))) {
    //     // rt.echo("your turn")
    //     // // if (!d["pStrs"][this.pIndex].includes("C") || d["phase"] != "initial") {
    //       // if (d["phase"] == "guessing")
    //
    //       const t = Math.round((d["scT"] - Date.now())/1000) - 1;
    //       // console.log("shot clock: ", d["scT"], t)
    //       this.termMain.promptCountdown(t)
    //       //   this.termMain.promptCountdown(8*(d["cBid"] - 1))
    //       // else
    //       //   this.termMain.promptCountdown(24, true);
    //       this.termSide.endCountdown();
    //       window.document.title = "Your Turn!"
    //       if (d["phase"] == "bidding") this.termMain.echo("Your turn - bid or fold.");
    //       if (d["phase"] == "guessing") this.termMain.echo("Your turn to guess.")
    //     // //}
    //     // alert("your turn!")
    //   } else {
    //     window.document.title = "zoom-hanabi"
    //     this.termMain.endPromptCountdown();
    //     const t = Math.round((d["scT"] - Date.now())/1000) - 1;
    //     this.termSide.countdown(t);
    //   }
    // } else {
    //   window.document.title = "zoom-hanabi"
    //   this.termMain.endPromptCountdown();
    //
    // }

  }
}

export {Ezgame}
