
from common import MYSQL, GADFLY, SQLITE

def escape_str(escape_tick, s):
    return s.replace("'", escape_tick)

class EscapeTick:
    def __init__(self, dbtype=None):
        self.escape_tick = "\\'"
        self.dbtype = dbtype
        if (dbtype): self.set(dbtype)

    def get(self):
        return self.escape_tick

    def set(self, dbtype):
        self.dbtype = dbtype
        if dbtype == SQLITE:
            self.escape_tick = "''"        

    def escape_str(self, s):
        return s.replace("'", self.escape_tick)
