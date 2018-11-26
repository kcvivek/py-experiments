import os, sys, string
from types import StringType
TEMPDIR = os.path.join("/", "tmp")
    
class IdentifierBase:
    def __init__(self, cursor, escape_tick, table, colval=None, colkey=None,
                 maxlen=None):
        self.cursor = cursor
        self.escape_tick = escape_tick
        self.table = table
        self.colval = colval or table + "_id"
        self.colkey = colkey or table
        self.maxlen = maxlen
        self.dict = {}
        self.nextid = self.get_nextid()
        

    def get_nextid(self):
        sql = "SELECT MAX(%s) AS num FROM %s" % (self.colval, self.table)
        try:
            #print sql
            self.cursor.execute(sql)
            val = int(self.cursor.fetchone()['num']) + 1
            #print "NEXTID:", val
            return val
        except Exception, e:
            #print "HERE:", e
            return 0


##    def get(self, key):
##        if type(key) == StringType:
##            key = string.replace(key, "'", escape_tick)
##            if self.maxlen:
##                key = key[:self.maxlen]

##        val = self.dict.get(key)
##        if val != None:
##            # returned cached value
##            return val
##        else:
##            cursor = self.cursor
##            try:
##                sql = "SELECT %s FROM %s WHERE %s = '%s'" % (self.colval,
##                                                             self.table,
##                                                             self.colkey,
##                                                             key)
##                cursor.execute(sql)
##            except Exception, e:
##                print str(e)
##                print "SQL Error:", sql
##                raise Exception, e
            
##            if cursor.rowcount:
##                # key is in db -- put it in dict and return val
##                val = self.cursor.fetchone()[self.colval]
##                self.dict[key] = val
##                return val
##            else:
##                # key is not in db -- insert it and return the value created
##                self.nextid += 1

##                sql = "INSERT INTO %s (%s, %s) VALUES(%d, '%s')" % (self.table,
##                                                                    self.colval,
##                                                                    self.colkey,
##                                                                    self.nextid,
##                                                                    key)
##                try:
##                    cursor.execute(sql)
##                except Exception, e:
##                    print sql
##                    print e

##                val = self.nextid
##                self.dict[key] = val
##                return val


    def get(self, key):
        if type(key) == StringType:
            key = self.escape_tick.escape_str(key)
            if self.maxlen:
                key = key[:self.maxlen]

        val = self.dict.get(key)
        if val != None:
            # returned cached value
            return val
        else:
            cursor = self.cursor
            try:
                sql = "SELECT %s FROM %s WHERE %s = '%s'" % (self.colval,
                                                             self.table,
                                                             self.colkey,
                                                             key)
                cursor.execute(sql)
            except Exception, e:
                print str(e)
                print "SQL Error:", sql
                raise Exception, e

            try:
                # key is in db -- put it in dict and return val
                val = self.cursor.fetchone()[self.colval]
                self.dict[key] = val
                return val
            except:
                if val == '-':   print sql
                # key is not in db -- insert it and return the value created
                self.nextid += 1
                
                sql = "INSERT INTO %s (%s, %s) VALUES(%d, '%s')" % (self.table,
                                                                    self.colval,
                                                                    self.colkey,
                                                                    self.nextid,
                                                                    key)
                try:
                    cursor.execute(sql)
                except Exception, e:
                    print sql
                    print e

                val = self.nextid
                self.dict[key] = val
                return val            


class IdentifierExtraBase(IdentifierBase):
    def __init__(self, cursor, escape_tick, table, colval=None,
                 colkey=None, colextra=None,
                 maxlen=None):
        self.colextra = colextra or "version"
        IdentifierBase.__init__(self, cursor, escape_tick, table, colval, colkey, maxlen)

        
##    def get(self, key, extrakey):
##        if type(key) == StringType:
##            key = string.replace(key, "'", escape_tick)
##            if self.maxlen:
##                key = key[:self.maxlen]

##        primaryval = self.dict.get(key)
##        if primaryval != None:
##            val = primaryval.get(extrakey)
##            if val != None:
##                # returned cached value
##                return val


##        cursor = self.cursor
##        try:
##            sql = "SELECT %s FROM %s WHERE %s = '%s' AND %s = '%s'" % \
##                  (self.colval,
##                   self.table,
##                   self.colkey,
##                   key,
##                   self.colextra,
##                   extrakey)
##            cursor.execute(sql)
##        except Exception, e:
##            print "Error in SQL:", sql
##            raise Exception, e

##        if cursor.rowcount:
##            # key is in db -- put it in dict and return val
##            val = self.cursor.fetchone()[self.colval]
##        else:
##            # key is not in db -- insert it and return the value created
###            self.fp.write("(%d, '%s', '%s'), " % (self.nextid, key, extrakey))
##            self.nextid += 1
##            val = self.nextid
##            sql = "INSERT INTO %s (%s, %s, %s) VALUES(%d, '%s', '%s')" % \
##                  (self.table,
##                   self.colval,
##                   self.colkey,
##                   self.colextra,
##                   self.nextid,
##                   key,
##                   extrakey)
##            try:
##                cursor.execute(sql)
##                val = self.nextid
##            except:
##                val = 0
##                print sql


##        try:
##            self.dict[key][extrakey] = val
##        except:
##            self.dict[key] = {extrakey: val}
##        return val


    def get(self, key, extrakey):
        if type(key) == StringType:
            key = self.escape_tick.escape_str(key)
            if self.maxlen:
                key = key[:self.maxlen]

        primaryval = self.dict.get(key)
        if primaryval != None:
            val = primaryval.get(extrakey)
            if val != None:
                # returned cached value
                return val


        cursor = self.cursor
        try:
            sql = "SELECT %s FROM %s WHERE %s = '%s' AND %s = '%s'" % \
                  (self.colval,
                   self.table,
                   self.colkey,
                   key,
                   self.colextra,
                   extrakey)
            cursor.execute(sql)
            #print sql
        except Exception, e:
            print "Error in SQL:", sql
            raise Exception, e

        try:
            val = self.cursor.fetchone()[self.colval]
        except:
            # key is not in db -- insert it and return the value created
#            self.fp.write("(%d, '%s', '%s'), " % (self.nextid, key, extrakey))

            self.nextid += 1
            val = self.nextid
            sql = "INSERT INTO %s (%s, %s, %s) VALUES(%d, '%s', '%s')" % \
                  (self.table,
                   self.colval,
                   self.colkey,
                   self.colextra,
                   self.nextid,
                   key,
                   extrakey)
            try:
                cursor.execute(sql)
                val = self.nextid
            except Exception, e:
                val = 0
                print sql
                print e


        try:
            self.dict[key][extrakey] = val
        except:
            self.dict[key] = {extrakey: val}
        return val


class FileTypeIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "file_type")

class SearchEngineIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "search_engine")

class SearchStringIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "search_string")

class SearchKeywordIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "search_keyword")

class SearchKeywordLogIdentifier(IdentifierExtraBase):
    def __init__(self, cursor, escape_tick):
        IdentifierExtraBase.__init__(self,
                                     cursor, escape_tick,
                                     "search_keyword_log",
                                     "search_keyword_log_id",
                                     "search_keyword_id",
                                     "log_id")

class RobotIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "robot")
    
class CountryIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "country")
    
class URLIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "url")
    
class RefererDomainIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "referer_domain")

class RefererPageIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "referer_page",
                                maxlen=128)

class RefererQSIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "referer_qs",
                                maxlen=255)

class IPAddrIdentifier(IdentifierExtraBase):
    def __init__(self, cursor, escape_tick):
        IdentifierExtraBase.__init__(self, cursor, escape_tick,
                                     "ip_addr",
                                     "ip_addr_id",
                                     "ip_addr",
                                     "hostname",
                                     maxlen=255)
    
class BrowserIdentifier(IdentifierExtraBase):
    def __init__(self, cursor, escape_tick):
        IdentifierExtraBase.__init__(self, cursor, escape_tick, "browser")


class OpSysIdentifier(IdentifierExtraBase):
    def __init__(self, cursor, escape_tick):
        IdentifierExtraBase.__init__(self, cursor, escape_tick, "op_sys")

class SessionIdentifier(IdentifierBase):
    def __init__(self, cursor, escape_tick):
        IdentifierBase.__init__(self, cursor, escape_tick, "session")


