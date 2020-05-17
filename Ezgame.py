import random
import time
import eventlet
import collections

random.seed()

class ShotClock:
    def __init__(self, cb):
        # self.ezgame = ezgame
        self.cb = cb
        self.handle = None
        # self.playerIndex = None
        self.maxTime = 25 # s
        self.endTime = None


    def reset(self):
        if self.handle != None:
            self.handle.cancel()
        t = self.maxTime
        self.endTime = time.time() + t
        self.handle = eventlet.spawn_after(t, self.shot_clock)


    def stop(self):
        if self.handle != None:
            self.handle.cancel()
            self.handle = None

    def shot_clock(self):
        self.cb()


class AIPlayer:
    def choose(self, data=None):
        pass

class AINines:
    def choose(self, data=None):
        return 9

class AIFives:
    def choose(self, data=None):
        return 5

class AIRandom:
    def choose(self, data=None):
        return random.randint(1,9)

class AI789:
    def choose(self, data=None):
        return random.randint(7,9)





class Round:
    def __init__(self, players, ai_choices):
        self.players = players
        self.choices = [None for p in self.players]
        self.ai_choices = ai_choices
        # [ap.choose() for ap in self.ai_players]


class Ezgame:
    def __init__(self, room):
        self.ev = "nines"
        self.room = room
        self.players = room.playing
        self.n = len(self.players)
        self.ai_players = [AINines(), AIFives(), AIRandom(), AI789()]
        self.ai_names = ["ai_rand", "ai_highs", "ai_fives", "ai_nines"]
        self.totaln = self.n + len(self.ai_players)
        self.end_score = 100
        self.round = None
        self.shotClock = ShotClock(self.end_round)
        self.cachedEmitData = None
        self.points = [0 for i in range(self.totaln)]
        self.history_strings = ["" for i in range(self.totaln)]
        self.is_over = False

        self.start_round()


    def start_round(self):
        aic = [ap.choose() for ap in self.ai_players]
        self.round = Round(self.players, aic)
        self.shotClock.reset()
        self.emit()
        # self.informInitial()


    # def run_ai(self):
    #     for ap in self.ai_players:
    #

    def end_round(self):
        winner = None
        r = self.round
        p_choices = [c if c != None else 0 for c in r.choices]
        actual_choices = p_choices
        actual_choices.extend(r.ai_choices)
        counter = collections.Counter(actual_choices)
        for i,c in enumerate(actual_choices):
            n = counter[c]
            pts = int(c/n)
            print(i,c,pts)
            self.points[i] += pts
            if self.points[i] >= self.end_score:
                winner = i
            chist = self.history_strings[i]
            nhist = chist + str(c)
            self.history_strings[i] = nhist[-8:]


        if winner != None:
            self.end_game(winner)

        if self.is_over == False:
            self.start_round()


    def end_game(self, w_index):
        print("end game: ", w_index)
        self.is_over = True
        self.emit()
    # const pl = self.round.getPlayerIndex(winnerIndex);
        # self.emit()
        self.room.end_game()



    def getSocket(self, i):
        return self.players[i].sid

    def get_index(self, sid):
        for i in range(self.n):
            if self.players[i].sid == sid: return i

    def io_handler(self, sid, data):
        print("ezgame io: ", sid, data)
        # i = self.get_index(sid)
        cp = self.room.find_player(sid=sid)
        if cp == None:
            self.room.notify_main("you're not even playing..", sid)
            return
        if self.ev in data:
            d = data[self.ev]
            if "choose" in d:
                self.choose(sid, d["choose"])
            # elif "skull" in sd:
            #     self.play(i, "skull")
            # elif "bid" in sd:
            #     self.bid(i, int(sd["bid"]))
            # elif "fold" in sd:
            #     self.fold(i)
            # elif "guess" in sd:
            #     self.guess(i, sd["guess"])


    def choose(self, sid, choice):
        try:
            sc = int(choice)
        except:
            self.room.notify_main("bad choice", sid)
            return

        if sc > 9 or sc < 0:
            self.room.notify_main("choice not in range", sid)
            return
        i = self.get_index(sid)
        if self.round.choices[i] == None:
            self.round.choices[i] = sc
        else:
            self.room.notify_main("you already chose", sid=sid)

        self.emit()

    def start(self):
        pass
        # self.informInitial()


    def initialData(self, sid):
        if self.cachedEmitData == None:
            self.emitData()
        i = self.get_index(sid)
        if i == None:
            name = None
        else:
            name = self.players[i].name
        ret = [name, i, self.cachedEmitData]
        return ret



    # def informInitial(self):
    #     for i in range(self.n):
    #         self.informTurn(i)


    # def informTurn(self, i=None):
    #     # pl = None
    #     # if p != None: pl = p
    #     # else pl = self.players[self.round.cpIndex]
    #     if i == None: i = self.round.cpIndex
    #     available = self.round.available[i]
    #     cards = self.round.cards[i]
    #     pl = self.players[i]
    #     if self.round.phase == "turns":
    #         self.room.emit_player(pl, ("yourTurn", cards, available))
    #     elif self.round.phase == "initial":
    #         self.room.emit_player(pl, ("initialPhase", cards, available))
    #
    #
    #
    # def endRound(self, i, outcome, sp):
    #     self.shotClock.stop()
    #     self.round.phase = "ended"
    #     print("endRound: ",i,outcome)
    #     self.room.emit_game("endRound")
    #     if outcome:
    #         self.points[i] += 1
    #     if self.points[i] == 2:
    #         self.endGame(i)
    #     else:
    #         eventlet.spawn_after(6, self.startRound, i)
    #         # print("set timeout")
    #         # setTimeout(self.startRound.bind(self, i), 6000)
    #
    #   # self.startRound(i);
    #
    #     if not outcome:
    #         # r = Math.floor(Math.random() * len(self.hands[i]))
    #         # self.hands[i].pop(r)
    #         self.hands[i].pop(random.randrange(len(self.hands[i])))
    #         if len(self.hands[i]) == 0:
    #             self.isAlive[i] = False
    #
    #         eventlet.spawn_after(6, self.startRound, sp)
    #         # setTimeout(self.startRound.bind(self, sp), 6000)
    #   # self.startRound(sp);
    #
    #
    #
    # def endGame(self, winnerIndex):
    #     print("end game: ", winnerIndex)
    # # const pl = self.round.getPlayerIndex(winnerIndex);
    #     self.emit()
    #     self.room.end_game()

    def emitData(self):
        # pNames = [cp.name for cp in self.players]
        # hLengths =  [len(hand) for hand in self.hands]
        #
        # r = self.round
        ret = {}
        ret["history_strings"] = self.history_strings
        ret["points"] = self.points
        public_choices = ["X" for i in range(self.n)] if self.is_over else ["N" if c != None else "_" for c in self.round.choices]
        public_choices.extend(["X" if self.is_over else "N" for i in range(len(self.ai_players))])
        ret["public_choices"] = public_choices
        pNames = [cp.name for cp in self.players]
        pNames.extend(self.ai_names)
        ret["pN"] = pNames
        ret["scT"] = self.shotClock.endTime*1000
        ret["is_over"] = self.is_over
        # ret["pts"] = self.points
        # ret["phase"] = r.phase
        # ret["cp"] = r.cpIndex
        # ret["status"] = r.status
        # ret["pStrs"] = self.publicStrings()
        # ret["bids"] = r.bids
        # ret["cBid"] = r.cBid
        # ret["nCards"] = r.nCards
        # ret["guessIndex"] = r.guessIndex
        # ret["cg"] = r.correctGuesses
        # ret["hLengths"] = hLengths
        # ret["scP"] = self.shotClock.playerIndex;
        # # ret["scT"] = self.shotClock.endTime*1000 if self.shotClock.endtime else None;
        # ret["scT"] = self.shotClock.endTime*1000
        self.cachedEmitData = ret
        return ret

    def emit(self):
        self.room.emit_game(("display", self.emitData()))
    # self.io.emit(self.ev, "display", self.emitData())
