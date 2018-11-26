try:
    import cPickle as pickle
except:
    import pickle
    
class FileBase:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        
        data = self.read_data()
        if data: self.data = data

    def dump_data(self):
        keys = self.data
        for key in keys:
            print key, ":", self.data[key]


    def read_data(self):
        try:
            fp = open(self.filename, "r")
        except Exception, e:
            print "Could not open", self.filename, str(e)
            return

        u = pickle.Unpickler(fp)
        try:
            data = u.load()
        except:
            data = {}
        fp.close()
        return data


    def write_data(self):
        try:
            fp = open(self.filename, "w")
        except:
            print "Could not write file:", self.filename
            return

        p = pickle.Pickler(fp)
        p.dump(self.data)
        fp.close()


    def get(self, key):
        dict = self.data.get(key)
        return dict
