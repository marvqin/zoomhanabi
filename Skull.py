# import {ServerModule, ClientModule} from "./Module.js"

class ShotClock:
    def __init__(self, skullServer):
        self.skullServer = skullServer
        self.handle = None
        self.playerIndex = None
        self.maxTime = 25000 # ms


    def reset(self, playerIndex):
        if self.handle != None:
            clearTimeout(self.handle)
        self.playerIndex = playerIndex
        t = self.maxTime
        if self.skullServer.round.phase == "guessing":
            t = 8*(self.skullServer.round.cBid - 1)*1000
        self.handle = setTimeout(self.shotClockViolation.bind(self), t)


    def shotClockViolation(self):
        r = self.skullServer.round
        ph = r.phase
        pi = r.cpIndex
        print("shot clock violation", r, ph, self.playerIndex)
        if ph == "initial":
          # for var i=0; i < r.players.length; i++:
            for i in range(len(r.players)):
                if r.isAlive[i] and len(r.cards[i]) == 0:
                    self.skullServer.notifyMain(r.players[i].name + " timed out and played a card.")
                    self.skullServer.play(i, r.available[i][0])

        elif ph == "turns":
            if self.playerIndex == r.cpIndex:
                c = r.available[pi][0]
            if c != None:
                self.skullServer.notifyMain(r.players[pi].name + " timed out and played a card (turns).")
                self.skullServer.play(pi, c)
            else:
                self.skullServer.notifyMain(r.players[pi].name + " timed out and bid 1.")
                self.skullServer.bid(pi, 1)

        elif ph == "bidding":
            if self.playerIndex == r.cpIndex:
                self.skullServer.notifyMain(r.players[pi].name + ": timed out and folded.")
                self.skullServer.fold(pi)

        elif ph == "guessing":
            if self.playerIndex == r.cpIndex:
                self.skullServer.notifyMain(r.players[pi].name + ": timed out and lost a card.")
                self.skullServer.endRound(pi, False, pi)


class Round:
    def __init__(self, players, startingIndex, available, isAlive):
        self.players = players
        self.phase = "initial"
        self.cards = []
        self.bids = []
        self.status = []
        self.cpIndex = startingIndex
        self.n = len(self.players)
        self.cBid = 0
        self.nCards = 0
        self.guessIndex = []
        self.available = available
        self.isAlive = isAlive
        self.correctGuesses = 0

        for cp in self.players:
            self.cards.append([])
            self.status.append(True)
            self.bids.append(0)
            self.guessIndex.append(-2)


    def allHavePlayed(self):
        if self.phase != "initial":
            print("bad allHavePlayed()")
        for i in range(self.n):
            if self.isAlive[i] and len(self.cards[i]) == 0:
                return False

        return True


    def findPlayerIndex(self, name):
        for i in range(self.n):
            if self.players[i].name == name:
                return i


# class ServerSkull extends ServerModule{
class ServerSkull:
    def __init__(self, room):
        self.ev = "skull"
        self.room = room
        self.players = room.playing
        self.n = len(self.players)
        self.round = None
        self.hands = []
        self.points = []
        self.isAlive = []
        self.shotClock = ShotClock(self)
        self.cachedEmitData = None

        for cp in self.players:
            self.hands.append(["skull", "rose", "rose", "rose"])
            self.points.append(0)
            self.isAlive.append(True)
        self.startRound(0)

    def getSocket(self, i):
        return self.players[i].sid

    def getIndex(self, sid):
        for i in range(self.n):
            if self.players[i].sid == sid: return i

    def io_handler(self, sid, data):
        print("skullioHandler", sid, data)
        i = self.getIndex(sid);
        if self.ev in data:
            sd = data[self.ev]
            if "rose" in sd:
                self.play(i, "rose")
            elif "skull" in sd:
                self.play(i, "skull")
            elif "bid" in sd:
                self.bid(i, int(sd["bid"]))
            elif "fold" in sd:
                self.fold(i)
            elif "guess" in sd:
                self.guess(i, sd["guess"])


    def start(self):
        self.informInitial()


    def initialData(self, sid):
        if self.cachedEmitData == None:
            self.emitData()
        i = self.getIndex(sid)
        p = self.players[i]
        ret = [p.name, i, self.cachedEmitData]
        return ret


    def startRound(self, sp):
    # var pl = [];
        availables = []
        for i in range(self.n):
            availables.append(self.hands[i].copy())

        self.round = Round(self.players, sp, availables, self.isAlive)
        self.emit()
        self.informInitial()
        # self.shotClock.reset()

    def canPlay(self, i, card):
        # print(i)
        if card not in self.round.available[i]:
            return False

        if self.round.phase == "initial" and len(self.round.cards[i]) == 0:
            return True

        if self.round.phase == "turns":
            return self.round.isCurrentPlayer(i)

        if self.round.phase == "bidding":
            return False


    def play(self, i, card):
        if self.canPlay(i, card):
            print("playing: ", i, card)
            self.round.cards[i].append(card)
            self.round.available[i].pop(self.round.available[i].index(card))
            self.round.nCards += 1
            if self.round.phase == "turns":
                self.nextPlayer()

            if self.round.phase == "initial" and self.round.allHavePlayed():
                self.round.phase = "turns"
                self.informTurn()
                # self.shotClock.reset(self.round.cpIndex)
                self.emit()

            else:
                self.room.notifyMain(self.getSocket(i), "cut the crap")


    def canBid(self, i, amount):
        print("canBid: ", i, amount)
        if amount != amount or amount <= 0 or amount > self.round.nCards:
            return False

        if self.round.phase == "initial":
            return False

        if self.round.phase == "turns":
            return self.round.isCurrentPlayer(i)

        if self.round.phase == "bidding":
            return (self.round.isCurrentPlayer(i) and amount > self.round.cBid)

    def bid(self, i, amount):
        if self.canBid(i, amount):
            self.round.bids[i] = amount
            self.round.cBid = amount
            self.round.phase = "bidding"
            self.nextPlayer()
        # self.shotClock.reset(self.round.cpIndex)
            self.emit()
        else:
            print("bad bid")


    def canFold(self, i):
        if not self.round.isCurrentPlayer(i):
            self.room.notifyMain(self.getSocket(i), "not your turn fool")
        return (self.round.isCurrentPlayer(i) and self.round.phase == "bidding")

    def fold(self, i):
        if self.canFold(i):
            self.round.status[i] = False
            self.nextPlayer()
            self.emit()


    def canGuess(self, i):
        if self.round.phase != "guessing":
             return False

        return self.round.isCurrentPlayer(i)

    def guess(self, i, name):
        if self.canGuess(i):
            index = self.round.findPlayerIndex(name)
            if index != None:
                gi = self.round.guessIndex[index]

            if gi >= 0:
                outcome = self.round.cards[index][gi]
                self.round.guessIndex[index] -= 1
                if outcome == "skull":
                    self.endRound(i, False, index)

                if outcome == "rose":
                    self.round.correctGuesses += 1
                if self.round.correctGuesses == self.round.cBid:
                    self.endRound(i, True)


            self.emit()



    def nextPlayer(self):
        if self.round.phase == "initial": return
        origIndex = self.round.cpIndex
        for i in range(self.n):
            self.round.cpIndex += 1
            if self.round.cpIndex == self.n:
                self.round.cpIndex = 0

            cpi = self.round.cpIndex
            if self.round.isAlive[cpi] and self.round.status[cpi]:
                break


        if self.round.phase == "bidding":
            cpi = self.round.cpIndex
            if self.round.bids[cpi] == self.round.cBid or origIndex == cpi:
                self.guessPhase()


        # self.shotClock.reset(self.round.cpIndex)
        self.informTurn()


    def informInitial(self):
        for i in range(self.n):
            self.informTurn(i)


    def informTurn(self, i=None):
        # pl = None
        # if p != None: pl = p
        # else pl = self.players[self.round.cpIndex]
        if i == None: i = self.round.cpIndex
        available = self.round.available[i]
        cards = self.round.cards[i]
        pl = self.players[i]
        if self.round.phase == "turns":
            self.room.emit_player(pl, ("yourTurn", cards, available))
        elif self.round.phase == "initial":
            self.room.emit_player(pl, ("initialPhase", cards, available))


    def guessPhase(self):
        self.round.phase = "guessing"
        self.round.guessIndex = []
        for cArray in self.round.cards:
            self.round.guessIndex.append(len(cArray) - 1)

        cpi = self.round.cpIndex
        for i in range(min(len(self.round.cards[cpi]), self.round.cBid)):
            self.guess(cpi, self.round.players[cpi].name)



    def endRound(self, i, outcome, sp):
        self.round.phase = "ended"
        print("endRound: ",i,outcome)
        self.room.emit_game("endRound")
        if outcome:
            self.points[i] += 1
        if self.points[i] == 2:
            self.endGame(i)
        else:
            setTimeout(self.startRound.bind(self, i), 6000)

      # self.startRound(i);

        if not outcome:
            r = Math.floor(Math.random() * len(self.hands[i]))
            self.hands[i].pop(r)
            if len(self.hands[i]) == 0:
                self.isAlive[i] = False

            setTimeout(self.startRound.bind(self, sp), 6000)
      # self.startRound(sp);



    def endGame(self, winnerIndex):
        print("end game: ", winnerIndex)
    # const pl = self.round.getPlayerIndex(winnerIndex);
        self.emit()
        self.room.end_game()

    def publicStrings(self):
        ret = []
        for cards,gi in zip(self.round.cards, self.round.guessIndex):
            iArray = []
            for j,card in enumerate(cards):
                c = None
                if card == "rose": c = "R"
                elif card == "skull": c = "S"
                if gi == -2 or gi >= j: c = "C"
                iArray.append(c)
            ret.append("".join(iArray))
        return ret

    def emitData(self):
        pNames = [cp.name for cp in self.players]
        hLengths =  [len(hand) for hand in self.hands]

        r = self.round
        ret = {}
        ret["pN"] = pNames
        ret["pts"] = self.points
        ret["phase"] = r.phase
        ret["cp"] = r.cpIndex
        ret["status"] = r.status
        ret["pStrs"] = self.publicStrings()
        ret["bids"] = r.bids
        ret["cBid"] = r.cBid
        ret["nCards"] = r.nCards
        ret["guessIndex"] = r.guessIndex
        ret["cg"] = r.correctGuesses
        ret["hLengths"] = hLengths
        self.cachedEmitData = ret
        return ret

    def emit(self):
        self.room.emit_game(("display", self.emitData()))
    # self.io.emit(self.ev, "display", self.emitData())

    def notifyMain(self, msg):
        self.room.emit_game(("notifyMain", msg))
