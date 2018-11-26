#!/usr/bin/env python

import sys, os, string
import script_common
from initial_sql import MySQLInit, SQLiteInit

common = script_common.ScriptCommon(0)
prefs = common.get_prefs()

dbname = prefs.get("DATA_NAME")

try:
    os.makedirs(os.path.join(os.pardir, prefs.get('DATA_DIR'), prefs.get('DATA_NAME')), 0700)
except OSError, e: 
    if e.args[0] != 17: # 17 = directory exists (which we can ignore)
        print e
        sys.exit(0)
except Exception, e:
    print e
    sys.exit(0)


database = prefs.get('DATABASE').lower()
if database == 'mysql':
    sqlInit = MySQLInit()
    sqlInit.set_db_name(dbname)
    
    dbconnection = common.connect()
    cursor = common.get_cursor()

    if common.get_drop_db():
        print "Dropping database: %s" % dbname
        try:
            common.execute("DROP database %s" % dbname)
        except:
            pass

    
elif database in ('sqlite', 'pysqlite'):
    sqlInit = SQLiteInit()

    drive, path = os.path.splitdrive(os.getcwd())

    datadir = prefs.get("DATA_DIR")
    drive, path = os.path.splitdrive(datadir)
    if path[0] != os.sep:
        path = os.path.join(os.pardir, path)

    dbpath = os.path.join(path, dbname, prefs.get('SQLITE_DB'))
    if common.get_drop_db():
        print "Dropping database: %s" % dbname
        try:
            os.remove(dbpath)
        except:
            pass

    dbconnection = common.connect(dbpath)
    cursor = dbconnection.cursor()
    common.set_cursor(cursor)





print "Creating Scratchy database %s (if necessary)" % dbname

#print dir(common.db)
#print common.db.get_server_info()


print "Creating Scratchy tables for %s database" % dbname
for clause in sqlInit.get_create_clauses():
    try:
        common.execute(clause)
    except Exception, e:
        print str(e)
        
for clause in sqlInit.get_insert_clauses():
    try:
        common.execute(clause, 0)
    except Exception, e:
        if e[0] != 1062:  # 1062 = duplicate
            print clause
            print str(e)
try:
    dbconnection.commit()
except:
    pass

try:
    dbconnection.close()
except:
    pass

