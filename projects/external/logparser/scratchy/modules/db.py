try:
    import MySQLdb
    import MySQLdb.cursors
    HAS_MYSQL = 1
except:
    HAS_MYSQL = 0

try:
    import sqlite
    HAS_PYSQLITE = 1
except:
    HAS_PYSQLITE = 0

try:
    import gadfly
    HAS_GADFLY = 1
except:
    HAS_GADFLY = 0
    
import os, sys, string
from types import StringType
from sql import *

def connect(prefs, sqlitepath=None):
    database = prefs.get('DATABASE').lower()

    if database == 'mysql':
        if not HAS_MYSQL: error("The MySQL python module is not installed")
            
        server = prefs.get('MYSQL_HOST')
        serverport = prefs.get('MYSQL_PORT')
        username = prefs.get('MYSQL_USERNAME')
        password = prefs.get('MYSQL_PASSWORD')
        dbname = prefs.get('DATA_NAME')
        if serverport:
            return MySQLdb.connect(db=dbname, host=server,
                                   user=username, passwd=password,
                                   port=serverport,
                                   cursorclass=MySQLdb.cursors.DictCursor)
        else:                        
            return MySQLdb.connect(db=dbname, host=server,
                                   user=username,
                                   passwd=password,
                                   cursorclass=MySQLdb.cursors.DictCursor)
    elif database in ('pysqlite', 'sqlite', 'sqllite'):
        if not HAS_PYSQLITE: error("The pysqlite module is not installed")
        if not sqlitepath:
            dataname = prefs.get('DATA_NAME')
            datadir = prefs.get('DATA_DIR')
            dbname = prefs.get('SQLITE_DB')
            sqlitepath = os.path.join(datadir, dataname, dbname)
            
        return sqlite.connect(sqlitepath, 774)
    elif database == 'gadfly':
        if not HAS_GADFLY: error("The gadfly module is not installed")
        dataname = prefs.get('DATA_NAME')
        datadir = prefs.get('DATA_DIR')
        return gadfly.gadfly(dataname, os.path.join(datadir, dataname))
    else:
        error("Unknown DATABASE specified in config file.  Currently, only mysql and pysqlite are supported")
        
def error(s):
    print s
    sys.exit(1)
    

def execute(cursor, sql):
    #print sql
    try:
        cursor.execute(sql)
    except Exception, e:
        print "SQL", sql
        print e
        raise Exception, e
        

def get_date_clause(first_clause="AND",
                    begdate=None,
                    enddate=None,
                    timestampcol="timestamp"):
    sql = ""
    if begdate:
        sql += " %s %s >= %d\n" % (first_clause, timestampcol, begdate)
    if enddate and first_clause is None:
        sql += " %s %s <= %d\n" % (first_clause, timestampcol, enddate)
    elif enddate:
        sql += " AND %s <= %d\n" % (timestampcol, enddate)

    return sql


def get_sql_str_for_log_stats(column, begdate=None, enddate=None,
                              sort_column=None, sort_order="DESC",
                              addl_where_crit=None):

    where = get_date_clause('WHERE', begdate, enddate)
    if addl_where_crit:
        if where:
            where = "%s\n AND %s " % (where, addl_where_crit)
        else:
            where = "AND " + addl_where_crit
    
        
    sql = """
    SELECT SUM(page) AS pages,
           SUM(bytes) AS bytes,
           COUNT(*) AS hits, 
           %s
    FROM log
    %s
    GROUP BY %s
    """ % (column, where, column)

    if sort_column:
        sql += " ORDER BY %s %s " % (sort_column, sort_order)

    return sql


def select_log_stats_dict(cursor, column, begdate=None, enddate=None, limit=None,
                          sort_column=None, sort_order="DESC"):
    # MAY NEED TO ADD "MORE" functionality...
    sql = get_sql_str_for_log_stats(column, begdate, enddate, sort_column, sort_order)
    
    dict = {}
    execute(cursor, sql)

    for i in range(cursor.rowcount):
        row = cursor.fetchone()
        try:
            key = row[column]
        except Exception, e:
            print "column:", column
            print "row:", row
            print "key:", key
            raise Exception, e
        dict[key] = {'hits': row['hits'], 'pages': row['pages'], 'bytes': row['bytes']}

    return dict

        
def select_log_stats_list(cursor, column, begdate=None, enddate=None, limit=None,
                          sort_column=None, sort_order="DESC",
                          addl_where_crit=None):

    sql = get_sql_str_for_log_stats(column,
                                    begdate,
                                    enddate,
                                    sort_column,
                                    sort_order,
                                    addl_where_crit)

    execute(cursor, sql)
    if limit:
        num = min(cursor.rowcount, limit)
    else:
        num = cursor.rowcount

    rows = cursor.fetchmany(num)
    more_dict = get_more(cursor)
        
    return rows, more_dict    


def select_ip_trace(cursor, ip_addr_id, begdate=None, enddate=None):
    sql = """
    SELECT url, referer_domain, referer_page, timestamp
    FROM log, url, referer_domain, referer_page
    WHERE log.url_id = url.url_id
    AND log.referer_domain_id = referer_domain.referer_domain_id
    AND log.referer_page_id = referer_page.referer_page_id
    AND ip_addr_id = %s
    ORDER BY timestamp
    """ % ip_addr_id
    execute(cursor, sql)
    return cursor.fetchall()


def select_totals(cursor, begdate=None, enddate=None):
        
    where = get_date_clause('WHERE', begdate, enddate)
        
    sql = """
    SELECT SUM(page) AS pages,
           SUM(bytes) AS bytes,
           COUNT(*) AS hits
    FROM log
    %s
    """ % where

    execute(cursor, sql)
    return cursor.fetchone()


def select_session_stats(cursor, ip_addr_id, begdate=None, enddate=None):
        
    where = get_date_clause('AND', begdate, enddate, "session_start")
        
    sql = """
    SELECT COUNT(*) AS num,
           MIN(session_start) AS first,
           MAX(session_start) AS last,
           MIN(session_duration) AS duration_min,
           MAX(session_duration) AS duration_max,
           AVG(session_duration) AS duration_avg
    FROM session
    WHERE ip_addr_id = %s
    %s
    """ % (ip_addr_id, where)

    #print sql
    execute(cursor, sql)
    session = cursor.fetchone()
    if session.get('num') == 0:
        session = {'num': 0,
                   'first': 0,
                   'last': 0,
                   'duration_min': 0,
                   'duration_max': 0,
                   'duration_min': 0 }
    return session

    
def select_browser_totals(cursor, begdate=None, enddate=None):
    sql = """
    SELECT COUNT(*) AS hits,
           SUM(page) AS pages,
           SUM(bytes) AS bytes
    FROM log
    WHERE browser_id IS NOT NULL
    """

    if begdate:
        sql += " AND timestamp >= %d" % begdate
    if enddate:
        sql += " AND timestamp <= %d" % enddate
        
    execute(cursor, sql)
    return cursor.fetchone()


def select_browser_versions(cursor, browser, begdate=None, enddate=None, limit=None):
    and_clause = ""
    if begdate:
        and_clause += " AND timestamp >= %d " % begdate
    if enddate:
        and_clause += " AND timestamp <= %d " % enddate

    sql = """
    SELECT COUNT(*) AS hits,
           SUM(page) AS pages,
           SUM(bytes) AS bytes,
           version
    FROM browser, log
    WHERE browser.browser_id = log.browser_id
    %s
    AND browser = '%s'
    GROUP BY browser, version
    ORDER BY browser, hits DESC
    """ % (and_clause, browser)

    execute(cursor, sql)

    if limit:
        num = min(cursor.rowcount, limit)
    else:
        num = cursor.rowcount
        
    rows = cursor.fetchmany(num)
    more_dict = get_more(cursor)
        
    return rows, more_dict    


def select_browser_versionsXXX(cursor, begdate=None, enddate=None, limit=None):
    and_clause = ""
    if begdate:
        and_clause += " AND timestamp >= %d " % begdate
    if enddate:
        and_clause += " AND timestamp <= %d " % enddate

    sql = """
    SELECT COUNT(*) AS hits,
           SUM(page) AS pages,
           SUM(bytes) AS bytes,
           browser,
           version
    FROM browser, log
    WHERE browser.browser_id = log.browser_id
    %s
    GROUP BY browser, version
    ORDER BY browser, hits DESC
    """ % (and_clause)

    execute(cursor, sql)
    dict = {}
    last_browser = None
    num = 0

    for i in range(cursor.rowcount):
        row = cursor.fetchone()
        browser = row['browser']
        inner_dict = {'hits': row['hits'],
                      'pages': row['pages'],
                      'bytes': row['bytes'],
                      'version': row['version']}

        if browser != last_browser:
            inner_dict['count'] = 1
            dict[browser] = [inner_dict]
            last_browser = browser
            num = 0
        else:
            if limit and num == limit:
                inner_dict['version'] = '__more__'
                inner_dict['count'] += 1
                dict[browser].append(inner_dict)
            elif limit and num > limit:
                xdict = dict[browser][-1]
                xdict['hits'] += inner_dict['hits']
                xdict['pages'] += inner_dict['pages']
                xdict['bytes'] += inner_dict['bytes']
                try:
                    xdict['count'] += 1
                except KeyError:
                    xdict['count'] = 1                    
            else:
                try:
                    if browser == '':
                        browser = 'None'
                        if not dict.has_key(browser):
                            dict[browser] = []
                    dict[browser].append(inner_dict)
                except:
                    print "browser:", browser, type(browser)
                    print "dict:", inner_dict
                    
            num += 1
    return dict


def get_referer_domain_clause(domains):
    if type(domains) == StringType:
        domain_str = "'%s'" % domains
    else:
        domain_str = ""
        for domain in domains:
            domain_str += "'%s', " % domain
        domain_str = domain_str[:-2]

    return domain_str


def select_access_method(cursor, domains, clause="IN", begdate=None, enddate=None):
    domain_str = get_referer_domain_clause(domains)

    sql = """
    SELECT SUM(page) AS pages,
           SUM(bytes) AS bytes,
           COUNT(*) AS hits
    FROM log, referer_domain AS R
    WHERE R.referer_domain %s (%s)
    AND log.referer_domain_id = R.referer_domain_id
    """ % (clause, domain_str)

    sql += get_date_clause("AND", begdate, enddate)
    execute(cursor, sql)

    data = cursor.fetchone()
    if data['pages'] is None: data['pages'] = 0
    if data['bytes'] is None: data['bytes'] = 0
    
    return data

         
##def XXXselect_hourly_stats(cursor):
##    sql = """
##    SELECT SUM(page) AS pages, SUM(bytes) AS bytes, COUNT(*) AS hits, hour
##    FROM log
##    GROUP BY hour
##    """

##    cursor.execute(sql)
##    dict = {}
##    # initialize dict
##    for i in range(24):
##        dict[i] = {'hits': 0, 'pages': 0, 'bytes': 0}

##    # insert result set into dict
##    for i in range(cursor.rowcount):
##        row = cursor.fetchone()
##        hour = row['hour']
##        dict[hour] = {'hits': row['hits'], 'pages': row['pages'], 'bytes': row['bytes']}
##    return dict



def select_joined_stats(cursor, tables, columns, limit=None,
                        begdate=None, enddate=None,
                        sort_col='hits', sort_order='DESC',
                        pages_only=0, addl_where_crit=None):
     
    if type(columns) == StringType:
        columns = [columns]

    if type(tables) == StringType:
        tables = [tables]
        
    cstr = ""
    for col in columns:
        cstr += col + ", "
    cstr = cstr[:-2]

    tstr = ""
    for table in tables:
        tstr += table + ", "
    tstr += "log"

    wstr = "%s.%s_id = log.%s_id " % (tables[0], columns[0], columns[0])
    if begdate:
        wstr += " AND timestamp >= %d" % begdate
    if enddate:
        wstr += " AND timestamp <= %d" % enddate

    if pages_only:
        wstr += " AND page = 1 "
    if addl_where_crit:
        wstr += addl_where_crit
        
    sql = """
    SELECT COUNT(*) AS hits, SUM(page) AS pages, SUM(bytes) AS bytes, %s
    FROM %s
    WHERE %s
    
    GROUP BY %s
    ORDER BY %s %s
    """ % (cstr, tstr, wstr, cstr, sort_col, sort_order)
    
    rows = []
    #print sql
    execute(cursor, sql)
    if limit:
        num = min(cursor.rowcount, limit)
    else:
        num = cursor.rowcount
    
    rows = cursor.fetchmany(num)
    
    more_dict = get_more(cursor)
    
    return rows, more_dict


def select_summary(cursor):
    sql = SELECT_SUMMARY

    execute(cursor, sql)

    return cursor.fetchall()
    

def select_error_urls(cursor,
                      error_code=None,
                      limit=None,
                      begdate=None,
                      enddate=None,
                      sort_col='hits',
                      sort_order='DESC'):

    if not error_code:
        error_code = "AND status_code >= 400"
    else:
        error_code = "AND status_code = %d" % error_code

    date_clause = get_date_clause("AND", begdate, enddate)

    sql = """
    SELECT COUNT(*) AS hits,
                       url,
                       status_code
    FROM log, url
    WHERE log.url_id = url.url_id
    %s
    %s
    GROUP BY status_code
    ORDER BY %s %s
    """ % (error_code, date_clause, sort_col, sort_order)

    rows = []
    execute(cursor, sql)
    if limit:
        num = min(cursor.rowcount, limit)
    else:
        num = cursor.rowcount

    rows = cursor.fetchmany(num)

    more_dict = get_more(cursor)
    return rows, more_dict


def select_search_keywords(cursor, limit=None,
                        begdate=None, enddate=None,
                        sort_col='hits', sort_order='DESC'):
     


    date_clause = get_date_clause("AND", begdate, enddate)

    sql = """
    SELECT SK.search_keyword,
           COUNT(*) AS hits,
           SUM(page) AS pages,
           SUM(bytes) AS bytes
    FROM log AS L, search_keyword AS SK, search_keyword_log AS SKL
    WHERE SKL.log_id = L.log_id
    AND SKL.search_keyword_id = SK.search_keyword_id
    %s
    GROUP BY SK.search_keyword
    ORDER BY %s %s
    """ % (date_clause, sort_col, sort_order)

    rows = []
    execute(cursor, sql)
    if limit:
        num = min(cursor.rowcount, limit)
    else:
        num = cursor.rowcount

    rows = cursor.fetchmany(num)
    more_dict = get_more(cursor)
        
    return rows, more_dict


def add_dicts(dict1, dict2):
    return {'hits': dict1['hits'] + dict2['hits'],
            'pages': dict1['pages'] + dict2['pages'],
            'bytes': dict1['bytes'] + dict2['bytes']}
   
            

def get_more(cursor):
    rows = cursor.fetchmany()
    if not rows: return None

    more = reduce(add_dicts, rows)

    return  {'count': len(rows),
            'hits': int(more.get('hits', 0)),
            'pages': int(more.get('pages', 0)),
            'bytes': int(more.get('bytes',0))}



def get_moreXXX(cursor):
    more_dict = {}
    more = [0,0,0,0] # count, hits, pages, bytes
    while 1:
        row = cursor.fetchone()
        if not row: break
        more[0] += 1
        more[1] += int(row['hits'])
        more[2] += int(row['pages'])
        more[3] += int(row['bytes'])

    if more[0] > 0: return {'count': more[0], 'hits': more[1], 'pages': more[2], 'bytes': more[3]}
    else:
        return None
    
##class DB:
##    def __init__(self, prefs):
##        try:
##            self.db = self.__connect(prefs)
##        except Exception, e:
##            print "Could not connect to scratchy database"
##            print str(e)
##            sys.exit(1)
        
##    def __connect(self):
##        server = prefs.get('MYSQL_HOST')
##        serverport = prefs.get('MYSQL_PORT')
##        username = prefs.get('MYSQL_USERNAME')
##        password = prefs.get('MYSQL_PASSWORD')

##        if serverport:
##            return MySQLdb.connect(db='', host=server,
##                                   user=username, passwd=password,
##                                   port=serverport,
##                                   cursor=MySQLdb.cursor.DictCursor)
##        else:                        
##            return MySQLdb.connect(db='', host=server,
##                                   user=username,
##                                   passwd=password,
##                                   cursor=MySQLdb.cursor.DictCursor)
                                   
