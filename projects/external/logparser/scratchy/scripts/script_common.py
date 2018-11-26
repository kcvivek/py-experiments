#  script-common.py: -*- Python -*-  DESCRIPTIVE TEXT.
import getopt
import sys
import os

try:
    import MySQLdb
    HAS_MYSQL = 1
except:
    HAS_MYSQL = 0

try:
    import sqlite
    HAS_SQLITE = 1
except:
    HAS_SQLITE = 0

try:
    import gadfly
    HAS_GADFLY = 1
except:
    HAS_GADFLY = 0


#modules_dir = os.path.join(os.pardir, "modules")
#sys.path.append(modules_dir)
sys.path.append(os.pardir)

#print "common path:", sys.path

from modules.prefs import Prefs
import modules.db

import getopt
    
class ScriptCommon:
    def __init__(self, auto_connect=1):
        config_file, drop_db, input_file  = self.parse_args()
        self.prefs = Prefs(config_file)
        self.drop_db = drop_db
        self.input_file = input_file
        self.cursor = None
        if auto_connect:
            self.connect()
            self.cursor = self.db.cursor()

    def get_input_file(self):
        return self.input_file
    
    def set_cursor(self, cursor):
        self.cursor = cursor
                    
    def get_cursor(self):
        if self.cursor:
            return self.cursor
        else:
            self.cursor = self.db.cursor()
            return self.cursor

    def execute(self, sql, print_sql=1):
        try:
            self.cursor.execute(sql)
        except Exception, e:
            if print_sql: print sql
            raise Exception, e
        
    def get_drop_db(self):
        return self.drop_db

    def get_prefs(self):
        return self.prefs
    
    def connect(self, sqlitepath=None):
        database = self.prefs.get("DATABASE").lower()

        if database == 'mysql' and HAS_MYSQL:
            dbname = self.prefs.get('DATA_NAME')
            server = self.prefs.get('MYSQL_HOST')
            serverport = self.prefs.get('MYSQL_PORT')
            username = self.prefs.get('MYSQL_USERNAME')
            password = self.prefs.get('MYSQL_PASSWORD')

            if serverport:
                self.db = MySQLdb.connect(db='',
                                          host=server,
                                          user=username,
                                          passwd=password,
                                          port=serverport)
            else:                        
                self.db = MySQLdb.connect(db='',
                                          host=server,
                                          user=username,
                                          passwd=password)
        elif database in ('sqlite', 'sqllite', 'pysqlite') and HAS_SQLITE:
            if not sqlitepath:
                dataname = self.prefs.get('DATA_NAME')
                datadir = self.prefs.get('DATA_DIR')
                dbname = self.prefs.get('SQLITE_DB')
                sqlitepath = os.path.join(datadir, dataname, dbname)
            #print os.path.abspath(sqlitepath)
            return sqlite.connect(sqlitepath, 774)
        elif database == 'gadfly' and HAS_GADFLY:
            return gadfly.gadfly()

        else:
            print "DATABASE must be set to sqlite or mysql in your config file"
            print "In addtion, you must install the appropriate database software"
            print "and Python module.\n"
            print "Please visit http://scratchy.sourceforge.net for more info"
            sys.exit(1)

    
    def usage(self):
        print "Usage: ", sys.argv[0], "[-c | --config=config_file] [--drop]"
        print
        print "The --drop option instructs the create script to first drop the"
        print "database specified in the config file first.  Use this option with"
        print "caution."
        print
        print "The config file defaults to ../config"
        
        sys.exit(0)


    def parse_args(self):
        args = sys.argv[1:]
        try:
            (opts, getopts) = getopt.getopt(args, 'c:i:?h',
                                            ["config=",
                                             "help",
                                             "input=",
                                             "drop"])
        except:
            print "\nInvalid command line option detected."
            self.usage()

        config_file = os.path.join(os.pardir, "config")
        drop_db = 0
        input_file = None
        
        for opt, arg in opts:
            #print opt, arg
            if opt in ('-h', '-?', '--help'):
                self.usage()
            if opt in ('-c', '--config'):
                config_file = arg
            if opt == '--drop':
                drop_db = 1
            if opt in ('-i', '--input'):
                input_file = arg
                
        return config_file, drop_db, input_file


