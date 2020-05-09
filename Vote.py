class Vote:
    def __init__(self, num_voters, cb):
        self.num_voters = num_voters
        self.cb = cb
        self.yes = []
        self.no = []


    def vote(self, name, v):
        if name in self.yes or name in self.no:
            return False
        if v == True:
            self.yes.append(name)
        else:
            self.no.append(name)

        if len(self.yes > self.num_voters/2):
            self.cb(True)
        elif len(self.no >= self.num_voters/2):
            self.cb(False)
