
class Terminal {
  constructor(term) {
    this.term = term
  }
  echo(s) {
    this.term.echo(s)
  }
  countdown(n) {
    this.timerN = n;
    this.term.echo(n);
    const fn = function() {
      // console.log(fn, this.timerN)
      this.timerN -= 1;
      if (this.timerN <= 0) window.clearInterval(this.intervalHandle)
      this.term.update(-1, this.timerN)
    }.bind(this);
    console.log("setting timer")
    this.intervalHandle = window.setInterval(fn, 1000)
  }
}
export {Terminal}
