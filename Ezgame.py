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
        self.maxTime = 30 # s
        # self.maxTime = 5
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

class AI789Cycle:
    def __init__(self):
        self.n = -1
    def choose(self, data=None):
        self.n += 1
        return (self.n % 3) + 7

class PowerupManager:
    def __init__(self):
        self.price_increase = 7
        self.price_decrease = 2
        self.prices = collections.OrderedDict()
        # self.prices["unlock19"] = 15
        # self.prices["instant-unlock19"] = 20
        # self.prices["steal"] = 25
        # self.prices["instant-steal"] = 35
        self.prices["invert"] = 20
        self.prices["instant-invert"] = 25

        self.global_powerups = ["invert", "instant-invert"]
        self.display_prices()

    def display_prices(self):
        self.powerup_names = list(self.prices.keys())
        self.powerup_prices = [str(self.prices[k]) for k in self.powerup_names]

    def buy(self, name):
        try:
            n = str(name)
        except:
            print("bad buy caught")
            return "","bad",0

        if n in self.prices:
            p = self.prices[n]
            # self.prices[n] += self.price_increase
            if n in self.global_powerups:
                return n,"global",p
            else:
                return n,"local",p
        else:
            return n,"bad",0

    def update(self, purchase_numbers):
        for k,v in self.prices.items():
            self.prices[k] -= self.price_decrease

        for k,v in purchase_numbers.items():
            self.prices[k] += self.price_increase*v
        self.display_prices()



class Round:
    def __init__(self, players, ai_choices, olddeltas, old_debts, old_recap_strings, old_dn):
        self.players = players
        self.choices = [None for p in self.players]
        self.ai_choices = ai_choices
        self.player_powerups = [[] for i in range(len(self.players))]
        self.global_powerups = []
        self.powerup_debt = [0 for i in range(len(self.players))]
        self.delayed_notifications = []
        self.purchase_number = collections.defaultdict(lambda: 0)
        self.deltas = [0 for i in range(len(self.players) + len(self.ai_choices))]
        self.olddeltas = olddeltas
        self.old_recap_strings = old_recap_strings
        self.recap_strings = []
        self.old_debts = old_debts
        self.debts = [0 for i in range(len(self.players))]
        self.old_delayed_notifications = old_dn
        # [ap.choose() for ap in self.ai_players]


class Ezgame:
    def __init__(self, room):
        self.ev = "nines"
        self.room = room
        self.players = room.playing
        self.n = len(self.players)
        self.ai_players = [AINines(), AIFives(), AIRandom(), AI789()]
        self.ai_names = ["ai_rand", "ai_highs", "ai_fives", "ai_nines"]
        self.ai_players = [AINines(), AI789Cycle()]
        self.ai_names = ["ai_rand", "ai_highs"]
        self.ai_players = []
        self.ai_names = []
        self.totaln = self.n + len(self.ai_players)
        self.end_score = 100
        self.round = None
        self.shotClock = ShotClock(self.end_round)
        self.cachedEmitData = None
        self.points = [0 for i in range(self.totaln)]
        self.history_strings = ["" for i in range(self.totaln)]
        self.is_over = False
        self.pm = PowerupManager()
        self.start_round()


    def start_round(self):
        self.room.emit_game("start_round")
        oldround = self.round
        aic = [ap.choose() for ap in self.ai_players]
        self.round = Round(self.players, aic, oldround.deltas if oldround else None, oldround.debts if oldround else None, oldround.recap_strings if oldround else [], oldround.delayed_notifications if oldround else [])

        if oldround != None:
            nglobals = ["instant-" + s for s in oldround.global_powerups if ("instant-" not in s) ]
            self.round.global_powerups.extend(nglobals)
            for s in oldround.global_powerups:
                if "instant-" in s:
                    continue
                else:
                    self.round.recap_strings.append("someone had previously bought {}".format(s))
            # self.round.old_recap_strings.append("{} used {}")

            for i,ps in enumerate(oldround.player_powerups):
                npl = ["instant-" + s for s in ps if "instant-" not in s]
                self.round.player_powerups[i].extend(npl)
                for s in ps:
                    if "instant-" in s:
                        continue
                    else:
                        self.round.recap_strings.append("{} had previously bought {}".format(self.players[i].name, s))

            print(self.round.global_powerups)
            print(self.round.player_powerups)

        self.shotClock.reset()
        self.emit()
        # self.informInitial()


    # def run_ai(self):
    #     for ap in self.ai_players:
    #

    def end_round(self):
        for i,debt in enumerate(self.round.powerup_debt):
            self.points[i] -= debt
            self.round.debts[i] -= debt
            # self.room.notify_main("you spent: {}".format(debt), self.getSocket(i))
        print("local ps: ", self.round.player_powerups)
        print("global ps: ", self.round.global_powerups)
        winner = None
        r = self.round
        p_choices = [c if c != None else 0 for c in r.choices]
        actual_choices = p_choices
        actual_choices.extend(r.ai_choices)
        counter = collections.Counter(actual_choices)

        n_invert = self.round.global_powerups.count("instant-invert")
        steal_choices = [c for c,ps in zip(r.choices, r.player_powerups) if "instant-steal" in ps]
        print("steal_choices: ",steal_choices)
        steal_counter = collections.Counter(steal_choices)
        for i,c in enumerate(actual_choices):
            steal_n = steal_counter[c]
            n = counter[c]

            if steal_n > 0:
                if i < len(self.round.player_powerups) and "instant-steal" in self.round.player_powerups[i]:
                    pts = int(c*(counter[c] + steal_counter[c])/steal_n)
                else:
                    pts = 0
            else:
                pts = int(c/n)
            pts = pts * (-1)**n_invert
            print(i,c,pts)
            self.points[i] += pts
            self.round.deltas[i] += pts
            # self.room.notify_main("you got: {}".format(pts), self.getSocket(i))
            if self.points[i] >= self.end_score:
                winner = i
            chist = self.history_strings[i]
            # if c > 0:
            #     nhist = chist + chr(9311+c)
            # else:
            #     nhist = chist + chr(10060)
            # if c > 0:
            nhist = chist + "{:02d} ".format(c)
            # else:
                # nhist = chist + chr(10060)
            # nhist = chist + str(c)
            self.history_strings[i] = nhist[-24:]
            # self.deltas[i] = pts


        if winner != None:
            self.start_round()
            self.end_game(winner)
            return

        if self.is_over == False:
            self.pm.update(self.round.purchase_number)

            dns = self.round.delayed_notifications
            self.start_round()
            # for dn in dns:
            #     self.room.notify_main(dn)


    def end_game(self, w_index):
        print("end game: ", w_index)
        self.is_over = True
        self.shotClock.stop()
        self.emit()
    # const pl = self.round.getPlayerIndex(winnerIndex);
        # self.emit()
        self.room.end_game()



    def getSocket(self, i):
        if i >= len(self.players):
            return -1
        else:
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
            if "buy" in d:
                self.buy(sid, d["buy"])
            # elif "skull" in sd:
            #     self.play(i, "skull")
            # elif "bid" in sd:
            #     self.bid(i, int(sd["bid"]))
            # elif "fold" in sd:
            #     self.fold(i)
            # elif "guess" in sd:
            #     self.guess(i, sd["guess"])


    def buy(self, sid, name):
        i = self.get_index(sid)
        if i == None:
            self.room.notify_main("what is this?", sid)
            return
        pname = self.players[i].name
        s, code, price = self.pm.buy(name)
        bought = False
        if code == "local":
            self.round.player_powerups[i].append(s)
            if "instant-" not in s:
                self.round.delayed_notifications.append("{} bought {}".format(pname, s))
            self.round.purchase_number[s] += 1
            bought = True
        elif code == "global":
            self.round.global_powerups.append(s)
            if "instant-" not in s:
                self.round.delayed_notifications.append("{} bought {}".format(pname, s))
            self.round.purchase_number[s] += 1
            bought = True
        else:
            self.room.notify_main("trash powerup", sid)
            return

        self.round.powerup_debt[i] += price
        if "instant-" in s:
            self.room.notify_main("{} is active immediately".format(s), sid)
            self.round.recap_strings.append("{} bought {}".format(pname, s))
        else:
            self.room.notify_main("{} will activate next turn".format(s), sid)
            # self.room.notify_main("{} bought {} for next turn".format(self.players[i].name, s))

    def choose(self, sid, choice):
        i = self.get_index(sid)
        if i == None:
            return
        try:
            sc = int(choice)
        except:
            self.room.notify_main("bad choice", sid)
            return

        if sc > 9 and sc < 20:
            if "instant-unlock19" not in self.round.player_powerups[i]:
                self.room.notify_main("you need to buy the powerup", sid)
                return
        elif sc > 9 or sc < 0:
                self.room.notify_main("choice not in range", sid)
                return

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

        # pn = list(self.pm.prices.keys())
        ret["powerup_names"] = self.pm.powerup_names
        ret["powerup_prices"] = self.pm.powerup_prices
        ret["deltas"] = [0 for i in range(self.totaln)] if self.round.olddeltas == None else self.round.olddeltas
        ret["recap_strings"] = self.round.old_recap_strings
        ret["debts"] = [0 for i in range(self.totaln)] if self.round.old_debts == None else self.round.old_debts + [0]*len(self.ai_players)
        ret["dns"] = self.round.old_delayed_notifications
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
