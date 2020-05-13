import eventlet
import time

class Vote:
    def __init__(self, voters, vote_type, vote_text, cb, t):
        self.voters = voters
        self.num_voters = len(voters)
        self.vote_type = vote_type
        self.vote_text = vote_text
        self.cb = cb
        self.yes = []
        self.no = []
        self.end_time = time.time() + t
        self.status = None
        self.handle = eventlet.spawn_after(t, self.timeout)


    def end(self, s):
        if self.handle != None:
            self.handle.cancel()
            # print("cb canceled")
        self.handle = None
        self.status = s
        self.cb(s)


    def timeout(self):
        # print("timeout")
        if len(self.yes) > len(self.no):
            self.end(True)
        else:
            self.end(False)

    def vote(self, name, v):
        if name in self.yes or name in self.no:
            return False
        if name not in self.voters:
            return False
        if v == True:
            self.yes.append(name)
        else:
            self.no.append(name)

        if len(self.yes) > self.num_voters/2:
            self.end(True)
        elif len(self.no) >= self.num_voters/2:
            self.end(False)

    def data(self):
        r = {}
        r["yes"] = len(self.yes)
        r["no"] = len(self.no)
        r["vote_text"] = self.vote_text
        r["vote_type"] = self.vote_type
        r["end_time"] = self.end_time*1000
        r["status"] = self.status
        r["total"] = self.num_voters
        return r
