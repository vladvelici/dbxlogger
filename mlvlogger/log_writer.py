
class LogWriter:
    def __init__(self, path):
        self.path = path
        self.f = open(self.path, "a")

    def serialise(self, log_entry):
        j = log_entry.json()
        print(j, file=self.f, end="\n")

    
