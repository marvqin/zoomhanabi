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


class HighcardPlayer:
    def __init__(self, room_player):
        self.room_player = room_player
        self.initial_chips = 100


class Stacks:
    def __init__(self, hplayers, chips):
        self.n = len(hplayers)
        self.hplayers = hplayers
        self.behind = chips.copy()
        self.committed = [0]*self.n
        self.betround_committed = [0]*self.n


    def set_bet(self, cp, b):
        self.behind[cp] -= b
        self.committed[cp] += b
        self.betround_committed[cp] += b


    def finish_betround(self):
        self.betround_committed = [0]*self.n


class BettingRound:
    def __init__(self, hplayers, stacks, cp_index, end_cb):
        self.hplayers = hplayers
        self.stacks = stacks
        self.cp_index = cp_index
        self.end_cb = end_cb
        self.c_bet = 0

        self.raiser_index = self.cp_index

        self.status = [True]*len(self.hplayers)
        # self.raiser_bet = 0


    def bet(self, b):
        cp = self.cp_index
        if b < cbet or b > self.stacks.chips(cp):
            raise ValueError("bad bet")
        self.stacks.set_bet(cp, b)
        self.c_bet = b
        self.next_player()

    def call(self):
        cp = self.cp_index
        if self.c_bet > self.stacks.chips(cp):
            self.stacks.all_in(cp)
        else:
            self.stacks.set_bet(cp, self.c_bet)
        self.next_player()

    def next_player(self):

        while True:
            self.cp_index += 1
            if self.cp_index == len(self.hplayers):
                self.cp_index = 0
            if self.status[self.cp_index] == True:
                break

        if self.cp_index == self.raiser_index:
            self.end_cb()


class OpeningRound(BettingRound):
    def __init__(self, hplayers, stacks, sb_index, end_cb):
        self.sb = 1
        self.bb = 2
        super().__init__(hplayers, stacks, sb_index, end_cb)
        self.bet(sb)
        self.bet(bb)


class Round:
    def __init__(self, hplayers, chips, sb_index):
        self.hplayers = hplayers
        self.chips = chips
        self.stacks = Stacks(hplayers, chips)
        self.sb_index = sb_index
        self.phase = "preflop"
        self.betting_round = OpeningRound(hplayers, self.stacks, sb_index, self.show_phase)
        # [ap.choose() for ap in self.ai_players]


    def show_phase(self):
        self.phase = "show"
        # self.betting_round = BettingRound(hplayers, self.stacks, sb_index, self.final_phase)

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
        self.cachedEmitData = ret
        return ret

    def emit(self):
        self.room.emit_game(("display", self.emitData()))
    # self.io.emit(self.ev, "display", self.emitData())
