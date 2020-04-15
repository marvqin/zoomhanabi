
class Command {
  constructor(command, fn) {
    if (Array.isArray(command)) {
      this.commandArray = command.slice();
    } else {
      this.commandArray = [command];
    }
    this.fn = fn;
  }
  run(c, ...data) {
    if (this.commandArray.includes(c)) {
      this.fn(...data);
      return true;
    }
  }
}

class Terminal {
  constructor(term) {
    this.term = term;
    this.cDict = {};
    this.mode = undefined;

    this.term.set_interpreter(this.handler.bind(this));

    this.countDownIntervalHandle = undefined;
    this.orig_prompt = undefined;
  }
  echo(s) {
    this.term.echo(s)
  }
  countdown(n) {
    this.timerN = n;
    this.term.echo(n);
    if (this.countDownIntervalHandle != undefined) window.clearInterval(this.countDownIntervalHandle);
    const fn = function() {
      // console.log(fn, this.timerN)
      this.timerN -= 1;
      if (this.timerN <= 0) window.clearInterval(this.countDownIntervalHandle)
      this.term.update(-1, this.timerN)
    }.bind(this);
    console.log("setting timer")
    this.countDownIntervalHandle = window.setInterval(fn, 1000)
  }
  endCountdown() {
    window.clearInterval(this.countDownIntervalHandle);
    if (this.countDownIntervalHandle != undefined)
      this.term.update(-1, "")
    this.countDownIntervalHandle = undefined;

  }
  promptCountdown(n, defer) {
    if (defer && this.promptCountDownIntervalHandle != undefined) return;
    this.promptTimerN = n;
    // const cp = this.term.get_prompt();
    // console.log(cp)
    // console.log(cp + this.promptTimerN.toString() + ": ")
    if (this.promptCountDownIntervalHandle != undefined) {
      window.clearInterval(this.promptCountDownIntervalHandle);
    }
    else {
      this.orig_prompt = this.term.get_prompt();
    }
    this.term.set_prompt(this.orig_prompt + this.promptTimerN.toString() + ": ");

    const fn = function() {
      // console.log(fn, this.promptTimerN)
      this.promptTimerN -= 1;
      this.term.set_prompt(this.orig_prompt + this.promptTimerN.toString() + ": ");
      if (this.promptTimerN <= 0) {
        this.endPromptCountdown();
        // this.term.set_prompt(this.orig_prompt);
        // window.clearInterval(this.promptCountDownIntervalHandle)
        // this.promptCountDownIntervalHandle = undefined;
        return;
      }

      // this.term.update(-1, this.promptTimerN)
    }.bind(this);
    console.log("setting timer")
    this.promptCountDownIntervalHandle = window.setInterval(fn, 1000)
  }
  endPromptCountdown() {
    this.term.set_prompt(this.orig_prompt);
    window.clearInterval(this.promptCountDownIntervalHandle)
    this.promptCountDownIntervalHandle = undefined;
  }
  addCommand(mode, command, fn) {
    if (this.cDict[mode] == undefined) this.cDict[mode] = [];
    this.cDict[mode].push(new Command(command, fn));
    console.log("addCommand", this)
  }
  showHelp() {
    const cArray = this.cDict[this.mode];
    for (var i=0; i < cArray.length; i++) {
      this.term.echo(cArray[i].commandArray.join(", "))
    }
  }
  handler(c) {
    const cs = c.slice(0, 256);
    var matched = false;
    try {
      var p = this.term.__T__.parse_command(cs);
      if (p.name == "help") {
        this.showHelp();
        matched = true;
      }
      console.log(this.cDict, this);
      const cArray = this.cDict[this.mode];
      for (var i=0; i < cArray.length; i++) {
        const m = cArray[i].run(p.name, ...p.args);
        if (m == true) matched = m;
      }
    }
    catch(err) {
      this.term.echo("bad command: "+err);
    }
    if (matched == false) this.term.echo("bad command")
    // if (matched == true) this.endPromptCountdown();
  }
}
export {Terminal}
