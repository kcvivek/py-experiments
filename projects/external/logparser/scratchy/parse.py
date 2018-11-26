#!/usr/bin/env python
import os
import os.path
import sys
import string
import re
import calendar
import getopt
import time
from urlparse import urlparse
from urllib import unquote_plus
from cgi import parse_qs
from copy import copy
from types import StringType, IntType
import gzip
import socket
#
#
import report
from modules.file_tracker import FileTracker
from modules.common import *
from modules.useragents import *
from modules.searchengines import SearchEngines
from modules.prefs import Prefs
import modules.output 
from modules.version import VERSION
import modules.db
from modules.identifier import *
from modules.sql import *
from modules.dictcursor import DictCursor
from modules.escape_tick import EscapeTick

try:
    import GeoIP
    HAS_GEOIP = 1
except Exception, e:
    HAS_GEOIP = 0

combined_format_re = re.compile(r'''(?P<host>.*?) -(?P<unknown>.*?)- \[(?P<date>.*?)\] "(?P<method>.*?) (?P<page>.*?)(?P<querystr>\?.*?)? (?P<protocol>.*?)" (?P<code>\d*) (?P<bytes>.*?) "(?P<referer>.*?)" "(?P<useragent>.*?)"''')

date_re = re.compile(r'''(?P<day>\d*)/(?P<month>.*)/(?P<year>\d*):(?P<hour>\d*):(?P<min>\d*):(?P<sec>\d*) *(?P<gmt_offset>.*)''')

useragent_re = re.compile(r"(?P<id>.*?)/(?P<version>[0-9\.]*)")

ip_address_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

# map month abbrevs to numeric equivalent
MONTH_MAP = {'Jan': 1,
             'Feb': 2,
             'Mar': 3,
             'Apr': 4,
             'May': 5,
             'Jun': 6,
             'Jul': 7,
             'Aug': 8,
             'Sep': 9,
             'Oct': 10,
             'Nov': 11,
             'Dec': 12}


class Log:
    def __init__(self, prefs,
                 log_filename=None,
                 rebuild=0,
                 noreport=0,
                 log_format_re=combined_format_re):

        self.prefs = prefs
        self.log_filename = log_filename
        self.rebuild = rebuild
        self.noreport = noreport
        self.data_dir = self.prefs.get('DATA_DIR')
        self.data_name = self.prefs.get('DATA_NAME')
        self.known_pages = self.prefs.get('KNOWN_PAGES', 1)
        self.known_aliases = self.prefs.get('KNOWN_ALIASES', 1)
        self.visit_time = self.prefs.get('VISIT_TIME')
        self.exclude_search_terms = self.prefs.get('EXCLUDE_SEARCH_TERMS', 1)
        self.__verbose = self.prefs.get('VERBOSE')
        self.__dns_cache = {}
        
        database = prefs.get('DATABASE').lower()
        if database == 'mysql':
            self.dbtype = MYSQL
            self.insert_log = self.insert_log_mysql
        elif database in ('pysqlite', 'sqlite', 'sqllite', 'pysqllite'):
            self.dbtype = SQLITE
            self.insert_log = self.insert_log_pysqlite
        elif database == 'gadfly':
            self.dbtype = GADFLY
            self.insert_log = self.insert_log_gadfly


        self.db = modules.db.connect(prefs)
        if self.dbtype == GADFLY:
            self.cursor = DictCursor(self.db)
        else:
            self.cursor = self.db.cursor()

        self.escape_tick = EscapeTick(self.dbtype)

        self.__last_date = None
        
        if log_format_re != None:
            self.set_log_format(log_format_re)
            
        calendar.setfirstweekday(calendar.SUNDAY)
        self.__user_agent_dict = {} # cache of useragents
        
        self.__tables = ('log',  'file_tracker', 'browser', 'country',
                         'file_type', 'ip_addr', 'op_sys', 'referer_domain',
                         'referer_page', 'referer_qs', 'robot',
                         'search_engine', 'search_keyword', 'search_keyword_log',
                         'search_string', 'session', 'url')


    def set_log_format(self, log_format_re):
        self.log_format_re = log_format_re


    def set_log_filename(self, log_filename):
        self.log_filename = log_filename

   
    def get_next_log_id(self, cursor):
        """
        Obtain the max log_id from log and then add 1 to it.
        If record doesn't exist, return 0.
        """
        sql = getsql(SELECT_MAX_LOG_ID, {})


        try:
            cursor.execute(sql)
            return cursor.fetchone()['num'] + 1
        except Exception, e:
            #print sql
            #print e
            return 0

    def get_next_session_id(self, cursor):
        """
        Obtain the max session_id from session and then add 1 to it.
        If record doesn't exist, return 0.
        """
        sql = getsql(SELECT_MAX_SESSION_ID, {})
        try:
            cursor.execute(sql)
            return cursor.fetchone()['num'] + 1
        except Exception, e:
            #print sql
            #print e
            return 1
        
        
    def process_log(self):
        """
        The workhorse method that iterates through the apache log, parses 
        and stores the results.
        """
        if not self.log_filename:
            raise Exception, "No log_filename provided"
        
        if self.log_filename.endswith(".gz"):
            fp = gzip.open(self.log_filename)
        else:
            fp = open(self.log_filename, "r")           



        cursor = self.cursor
        db = self.db
        escape_tick = self.escape_tick

        if self.dbtype == MYSQL:
            self.lock_tables(cursor)

        first_log_id = log_id = self.get_next_log_id(cursor)

        file_typeID = FileTypeIdentifier(cursor, escape_tick)
        browserID = BrowserIdentifier(cursor, escape_tick)
        robotID = RobotIdentifier(cursor, escape_tick)
        op_sysID = OpSysIdentifier(cursor, escape_tick)
        countryID = CountryIdentifier(cursor, escape_tick)
        refererDomainID = RefererDomainIdentifier(cursor, escape_tick)
        refererPageID = RefererPageIdentifier(cursor, escape_tick)
        refererQSID = RefererQSIdentifier(cursor, escape_tick)
        ip_addrID = IPAddrIdentifier(cursor, escape_tick)
        urlID = URLIdentifier(cursor, escape_tick)
        search_engineID = SearchEngineIdentifier(cursor, escape_tick)
        search_stringID = SearchStringIdentifier(cursor, escape_tick)
        search_keywordID = SearchKeywordIdentifier(cursor, escape_tick)
        search_keyword_logID = SearchKeywordLogIdentifier(cursor, escape_tick)

        start_time = time.time()
        parsed_lines = 0
        total_lines = 0
        epoch = 0

        ip_trace_enabled = self.prefs.get('ENABLE_IP_TRACE')
        country_lookup = self.prefs.get('COUNTRY_LOOKUP')

        country_cache = None
        if HAS_GEOIP and country_lookup:
            country_cache = GeoIP.open(self.prefs.get('GEOIP_DB'),
                                       GeoIP.GEOIP_STANDARD)
        elif country_lookup:
            print ">>   WARNING: Could not load GeoIP module:"
            print "..   IP address to country name lookups will be disabled"
            print "..   To disable this warning, edit your config file"
            print "..   and set COUNTRY_LOOKUP to 0."
            print

        fp.seek(0, 2)
        file_size = fp.tell()
        fp.seek(0)
        line = fp.readline()
        if line:
            first_line = line

            file_tracker = FileTracker(cursor, escape_tick)
            ft_data = file_tracker.get(first_line)
            if not ft_data:
                file_tracker_id = file_tracker.insert(first_line, file_size)
                #print file_tracker_id
            else:
                file_tracker_id = ft_data['file_tracker_id']
                if self.rebuild:
                    start_offset = 0
                    self.delete_log_entries(cursor, file_tracker_id)
                else:
                    start_offset = ft_data['file_offset']
                    fp.seek(start_offset)
        else:
            first_line = None
            start_offset = 0


        if self.dbtype == MYSQL:
            major_version = self.get_mysql_version(db)
            #self.lock_tables(cursor)
            if major_version > 3: self.disable_keys(cursor)
            try:
                batch_fp = open(self.prefs.get("TMP_FILE"), "w")
            except:
                print "Could not write to temporary batch file:",
                print self.prefs.get("TMP_FILE")
                self.unlock_tables(cursor)
                sys.exit(1)
            xparam = batch_fp
        elif self.dbtype == SQLITE:
            xparam = cursor
        elif self.dbtype == GADFLY:
            batch_list = []
            xparam = batch_list
        

        parsed_dates = []
        month_start_time = None
        try:
            while 1:
                line = fp.readline()
                if not line:
                    break

                total_lines += 1
                m = self.log_format_re.search(line)
                if m:
                    parsed_lines += 1
                    date = m.group('date')

                    date, day_of_month, day_of_week, hour, epoch, month, year = \
                          self.__parse_date(date)

                    date_tuple = (month, year)
                    if date_tuple != self.__last_date:
                        if self.__verbose:
                            if month_start_time:
                                print ".. [ completion time: %d seconds ]" % \
                                      (time.time() - month_start_time)
                            print ">>    Parsing date: %s/%s" % (date_tuple[0],
                                                                 date_tuple[1])
                        parsed_dates.append(date_tuple)
                        self.__last_date = date_tuple
                        month_start_time = time.time()

                    host = m.group('host')
                    page = m.group('page')
                    try:
                        bytes = int(m.group('bytes'))
                    except:
                        bytes = 0

                    file_type = self.__get_file_type(page)

                    page_count = self.__get_page_count(file_type)
                    useragent = m.group('useragent')

                    useragent_dict = self.__process_useragent(useragent)
                    if useragent_dict:
                        robot_id = robotID.get(useragent_dict['robot'])
                        browser_id = browserID.get(useragent_dict['browser'],
                                                   useragent_dict['browser_version'])
                        op_sys_id = op_sysID.get(useragent_dict['op_sys'],
                                                 useragent_dict['op_sys_version'])
                    else:
                        robot_id = browser_id = op_sys_id = 0

                    file_type_id = file_typeID.get(file_type)

                    ip_addr, hostname = self.ip_lookup(host)
                    ip_addr_id = ip_addrID.get(ip_addr, hostname)
                    url_id = urlID.get(page)

                    code = int(m.group('code'))
                    referer = m.group('referer')
                    referer_domain, referer_page, referer_qs = self.__get_referer(referer)
                    referer_domain_id = refererDomainID.get(referer_domain)
                    referer_page_id = refererPageID.get(referer_page)
                    referer_qs_id = refererQSID.get(referer_qs)

                    search = self.__get_search_engine(referer_domain, referer_qs)
                    if search:
                        search_engine_id = search_engineID.get(search[0].get('name'))
                        search_string_id = search_stringID.get(search[1])
                        for kywrd in search[2]:
                            search_keywords.append(kywrd)
                    else:
                        search_engine_id = 0
                        search_string_id = 0
                        search_keywords = []

                    if country_cache:
                        if ip_addr:
                            country = country_cache.country_name_by_addr(ip_addr)
                        else:
                            country = country_cache.country_name_by_name(hostname)
                        if not country: country_id = 0
                        else:           country_id = countryID.get(country)
                    else:
                        country_id = 0

                    if not self.insert_log(xparam, log_id, file_tracker_id, epoch,
                                           page_count, bytes, code, hour, day_of_week,
                                           country_id, url_id, ip_addr_id, op_sys_id,
                                           robot_id, browser_id, file_type_id,
                                           search_engine_id, search_string_id,
                                           day_of_month, month, year,
                                           referer_domain_id, referer_page_id,
                                           referer_qs_id): continue

                    for kywrd in search_keywords:
                        search_keyword_id = search_keywordID.get(kywrd)
                        search_keyword_logID.get(search_keyword_id, log_id)
                        
                    if self.dbtype == MYSQL: cursor.execute("commit")
                    else: pass
                        #if log_id % 100: db.commit()
                    log_id += 1
                else:
                    pass
                    #print line
        except Exception, e:
            print e

        
        if self.__verbose and month_start_time:
            print ".. [ completion time: %d seconds ]" % \
                  (time.time() - month_start_time)

        last_log_id = log_id
        file_offset = fp.tell()
        fp.close()
        if total_lines:
            file_tracker.set(first_line, file_size, file_offset)

        #if country_cache_ttl: country_cache.write_data()
        
        if self.dbtype == MYSQL:
            batch_fp.close()
            self.insert_log_data_mysql(cursor)
        elif self.dbtype == GADFLY:
            self.insert_log_data_gadfly(batch_list, cursor)

        parse_secs = time.time() - start_time

        if self.dbtype == MYSQL:
            if major_version > 3: self.enable_keys(cursor)
            self.unlock_tables(cursor)
            try:
                os.remove(self.prefs.get("TMP_FILE"))
            except Exception, e:
                print "WARNING: Could not delete tmp_file:", self.prefs.get("TMP_FILE")
        elif self.dbtype in (SQLITE, GADFLY):
            if self.__verbose: "Committing data"
            db.commit()
        
        
        print
        print ">> Processing summary:"
        print ".. Parsed lines             :", total_lines
        print ".. Parse time               : %.2f" % parse_secs
        try:
            print ".. Parsed lines/sec         : %.2f" % (float(total_lines) / parse_secs)
        except:
            pass
        nsecs = time.time() - start_time
        print ".. Completion time (seconds): %.2f" % nsecs
        try:
            print ".. Lines per second         : %.2f" % (float(total_lines) / nsecs)
        except:
            pass

        return parsed_dates


    def insert_log_mysql(self, batch_fp, log_id, file_tracker_id, epoch, page_count,
                         bytes, code, hour, day_of_week, country_id, url_id,
                         ip_addr_id, op_sys_id,  robot_id, browser_id, file_type_id,
                         search_engine_id, search_string_id, day_of_month, month, year,
                         referer_domain_id, referer_page_id, referer_qs_id):
        batch_fp.write("(%d, %d, %ld, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d)\n" % \
                       (log_id, file_tracker_id, epoch, page_count, bytes, code,
                        hour, day_of_week, country_id, url_id,
                        ip_addr_id, op_sys_id, robot_id, browser_id,
                        file_type_id, search_engine_id,
                        search_string_id, day_of_month, month, year,
                        referer_domain_id, referer_page_id, referer_qs_id))
        return 1


    def insert_log_pysqlite(self, cursor, log_id, file_tracker_id, epoch, page_count,
                            bytes, code, hour, day_of_week, country_id, url_id,
                            ip_addr_id, op_sys_id,  robot_id, browser_id,
                            file_type_id, search_engine_id,
                            search_string_id, day_of_month, month, year,
                            referer_domain_id, referer_page_id, referer_qs_id):

        sql = """
        INSERT INTO log
        (log_id, file_tracker_id, timestamp, page,
        bytes, status_code, hour, day_of_week,
        country_id, url_id, ip_addr_id, op_sys_id,
        robot_id, browser_id, file_type_id, search_engine_id,
        search_string_id, day_of_month, month, year, 
        referer_domain_id, referer_page_id, referer_qs_id)
        VALUES(%d, %d, %ld, %d,
        %d, %d, %d, %d,
        %d, %d, %d, %d,
        %d, %d, %d, %d,
        %d, %d, %d, %d,
        %d, %d, %d)
        """ % (log_id, file_tracker_id, epoch, page_count,
               bytes, code, hour, day_of_week,
               country_id, url_id, ip_addr_id, op_sys_id,
               robot_id, browser_id, file_type_id, search_engine_id,
               search_string_id, day_of_month, month, year,
               referer_domain_id, referer_page_id, referer_qs_id)

        file = open(self.prefs.get("TMP_FILE"), "a")
        file.write("%s;\n" % sql)
        file.close()
        try:
            modules.db.execute(cursor, sql)
            return 1
        except Exception, e:
            print e
            return 0
                                 

    def insert_log_gadfly(self, blist, log_id, file_tracker_id, epoch, page_count, bytes,
                          code, hour, day_of_week, country_id, url_id,
                          ip_addr_id, op_sys_id,  robot_id, browser_id, file_type_id,
                          search_engine_id, search_string_id, day_of_month, month, year,
                          referer_domain_id, referer_page_id, referer_qs_id):
        blist.append((log_id, file_tracker_id, epoch, page_count, bytes, code,
                      hour, day_of_week, country_id, url_id,
                      ip_addr_id, op_sys_id, robot_id, browser_id,
                      file_type_id, search_engine_id,
                      search_string_id, day_of_month, month, year,
                      referer_domain_id, referer_page_id, referer_qs_id))
        return 1


    def delete_log_entries(self, cursor, file_tracker_id):
        """
        If --rebuild was specified, remove log_ids from log and
        search_keyword_log tables that exist between the specifed log_id range.
        """

        if self.__verbose:
            print ">> Rebuild mode enabled..."
            print ".. Deleting entries from log table"

        sql = """
        SELECT log_id
        FROM log
        WHERE file_tracker_id = %d
        """ % file_tracker_id

        cursor.execute(sql)
        results = cursor.fetchall()
        if not results:
            if self.__verbose: print ".. No entries to delete"
            return

        log_ids_str = ""
        for result in results:
            log_ids_str += "%ld, " % result['log_id']
        log_ids_str = log_ids_str[:-2]


        sql = """
        DELETE FROM log
        WHERE log_id IN (%s)
        """ % log_ids_str

        #print sql
        cursor.execute(sql)

        if self.__verbose: print ".. Deleting entries from search_keyword_log table"
        sql = """
        DELETE FROM search_keyword_log
        WHERE log_id IN (%s)
        """ % log_ids_str

        cursor.execute(sql)


    def insert_log_data_mysql(self, cursor):
        batch_fp = open(self.prefs.get("TMP_FILE"), "r")
        i = 0
        if self.__verbose:
            print ">> Inserting log table chunks: "
            start_time = time.time()
        while 1:
            batchlines = batch_fp.readlines(1000000)
            if not batchlines: break
            if self.__verbose:
                sys.stdout.write("\r.. Chunk: %d" % i)
                sys.stdout.flush()


            i += 1
            sql =  """
            INSERT INTO log
            (log_id, file_tracker_id, timestamp, page,
            bytes, status_code, hour, day_of_week,
            country_id, url_id, ip_addr_id, op_sys_id,
            robot_id, browser_id, file_type_id, search_engine_id,
            search_string_id, day_of_month, month, year, 
            referer_domain_id, referer_page_id, referer_qs_id)
            VALUES %s""" % string.join(batchlines, ', ')
            cursor.execute(sql)
            
        if self.__verbose:
            print
            print ".. [ completion time: %.2f seconds ]" % (time.time() - start_time)


    def insert_log_data_gadfly(self, blist, cursor):
        sql = """
        INSERT INTO log
        (log_id, file_tracker_id, timestamp, page,
        bytes, status_code, hour, day_of_week,
        country_id, url_id, ip_addr_id, op_sys_id,
        robot_id, browser_id, file_type_id, search_engine_id,
        search_string_id, day_of_month, month, year, 
        referer_domain_id, referer_page_id, referer_qs_id)
        VALUES (?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?)"""

        cursor.execute(sql, blist)



    def lock_tables(self, cursor):
        sql = "LOCK TABLES "
        for table in self.__tables:
            sql += "%s WRITE, " % table
        sql = sql[:-2]
        cursor.execute(sql)

    def unlock_tables(self, cursor):
        sql = "UNLOCK TABLES"
        cursor.execute(sql)


    def get_mysql_version(self, db_connection):
        vers =  db_connection.get_server_info()
        return int(vers[0]) # returns major version # (eg. 3, 4,etc...)


    def __toggle_keys(self, cursor, action="disable"):
        if self.__verbose:
            if action == "disable": s = "Disabling"
            else:                   s = "Enabling"
            print ">> %s keys for all tables" % s
            start_time = time.time()
        if action == "disable": sqlaction = "DISABLE KEYS"
        else:                   sqlaction = "ENABLE KEYS"
        for table in self.__tables:
            sql = "ALTER TABLE %s %s" % (table, sqlaction)
            cursor.execute(sql)
        if self.__verbose:
            print ".. [ completion time: %d seconds ]" % (time.time() - start_time)


    def disable_keys(self, cursor):
        self.__toggle_keys(cursor, "disable")
            
    def enable_keys(self, cursor):
        self.__toggle_keys(cursor, "enable")


    def create_reports(self, date_tuples):
        if not date_tuples: return
        if self.__verbose: print "\n>> CREATING REPORTS\n"
        
        for date_tuple in date_tuples:
            r = report.Report(date_tuple[0],
                              date_tuple[1],
                              self.prefs,
                              self.cursor)
        if date_tuples:
            r.create_summary()


    def delete_sessions(self, month, year):
        if self.__verbose: print ".. Deleting sessions for %d/%d" % (month, year)
        sql = """
        DELETE FROM session
        WHERE month = %d
        AND year = %d
        """ % (month, year)
        self.cursor.execute(sql)


    def get_session_data(self, month, year):
        sql = """
        SELECT  ip_addr_id,
                timestamp
        FROM    log
        WHERE   month = %d
        AND     year = %d
        ORDER BY ip_addr_id, timestamp asc
        """ % (month, year)

        if self.__verbose: print ".. Getting session data from log"
        self.cursor.execute(sql)        
        rows = self.cursor.fetchall()
        if not rows: return None

        ip_dict = {}
        for row in rows:
            try:
                ip_dict[row['ip_addr_id']].append(row['timestamp'])
            except:
                ip_dict[row['ip_addr_id']] = [row['timestamp']]
        return ip_dict


 
    def insert_sessions(self, month, year):
        rows = self.get_session_data(month, year)
        if not rows: return

        sessions = []
        session = None

        if self.__verbose: print ".. inserting session data into session table"
        session_timeout = self.prefs.get("VISIT_TIME")
        tuples = rows.items()
        session_id = self.get_next_session_id(self.cursor)
        for ip_addr, timestamps in tuples:
            session = {'ip_addr_id': ip_addr,
                       'session_start': timestamps[0]}
            last_timestamp = timestamps[0]
            timestamps.append(None)
            for timestamp in timestamps[1:]:
                if timestamp and timestamp - last_timestamp > session_timeout or not timestamp:
                    session['session_id'] = session_id
                    session['session_end'] = last_timestamp
                    session['session_duration'] = last_timestamp - session['session_start']
                    session['month'] = month
                    session['year'] = year
                    sql = getsql(INSERT_SESSION, session)
                    self.cursor.execute(sql)

                    session_id += 1

                    if timestamp:
                        session = {'ip_addr_id': ip_addr,
                                   'session_start': timestamp}

                last_timestamp = timestamp

                
            

    def compute_sessions(self, date_tuples):
        if not date_tuples: return
        if self.__verbose: print ">> Compiling session information"
        for date_tuple in date_tuples:
            self.delete_sessions(date_tuple[0], date_tuple[1])
            self.insert_sessions(date_tuple[0], date_tuple[1])



    def dump_stats(self):
        output.output(self.parsed_data)
        #output.output(self.parsed_data['file_type'])


    def __process_useragent(self, useragent):
        if useragent == '-': return None

        dict = self.__user_agent_dict.get(useragent)
        if dict:
            return dict
        
        luseragent = string.lower(useragent)
        _opsys = ''
        _opsys_vers = ''
        _robot = ''
        _browser = ''
        _browser_vers = ''

        robots_re = get_robots_regex()

        m = winie_re.search(useragent)
        if m:
            _browser = m.group('browser').lower()
            _browser_vers = m.group('version')
            opsys = m.group('os')
            _opsys_vers = m.group('osvers')
            
            _opsys = OPERATING_SYS.get(opsys + " " + _opsys_vers, '')
            #print _browser, _browser_vers
        else:
            # not Windows + IE
            info = parse_special_browser(luseragent)
            if info:
                _browser = info[0]
                try:
                    _browser_vers = info[1]
                except:
                    _browser_vers = ""
                #print _browser, _browser_vers
            else:
                # not a browser? 
                pass

            m = opsys_re.search(useragent)
            if m:
                opsys = useragent[m.start():m.end()]
                _opsys = OPERATING_SYS.get(opsys, '')
            elif string.find(useragent, 'X11') >= 0:
                _opsys = OPERATING_SYS.get('X11', '')
            else:
                m = robots_re.search(luseragent)
                if m:
                    robot = luseragent[m.start():m.end()]
                    _robot = ROBOTS.get(robot, '')
                else:
                    pass  #print "Unknown os/robot:", useragent

        if not _browser and not _robot: # and not _opsys: 
            m = generic_browser_re.search(luseragent)
            if m:
                _browser = m.group('browser')
                if not _browser:
                    pass
                    #print "agent", luseragent
                _browser_vers = m.group('version')
                #print _browser, _browser_vers
            else:
                print "Could not recognize useragent:", useragent
                return None


        dict = {'robot': _robot,
                'op_sys': _opsys,
                'op_sys_version': _opsys_vers,
                'browser': _browser,
                'browser_version': _browser_vers}

        self.__user_agent_dict[useragent] = dict
        return dict

    
    def __get_page_count(self, file_type):
        if file_type in self.known_pages or file_type == None:
            return 1
        else:
            return 0
        
            
    def __get_file_type(self, page):
        urltuple = urlparse(page)

        try:
            idx = string.rindex(urltuple[2], ".")
            file_type = urltuple[2][idx+1:]
            if len(file_type) > 10:
                file_type = "Unknown"
            return file_type            
        except:
            pass

        return "html"


    def __parse_date(self, date):
        m = date_re.search(date)
        if m:
            #gmt_offset = int(m.group('gmt_offset'))
            hour = int(m.group('hour'))
            min = int(m.group('min'))
            sec = int(m.group('sec'))
            day = int(m.group('day'))
            month = m.group('month')
            imonth = MONTH_MAP[month]
            year = int(m.group('year'))
            
            epoch = long(time.mktime( (year, imonth, day, hour, min, sec,0,0,0) ))
            date = "%s %d, %d" % (month, day, year)
            day_of_week = calendar.weekday(year, imonth, day)

            return date, day, day_of_week, hour, epoch, imonth, year
        return None, None, None, None, None, None, None


    def __compute_summary(self, month, year, pages, hits, bytes):
        #? 
        dict = self.parsed_data['summary']
        dict['month'] = month
        dict['year'] = year
        dict['bytes'] += bytes
        dict['pages'] += pages
        dict['hits'] += hits

        
    def __get_referer(self, referer):
        if referer == '-': return referer, '', ''
        referer = string.replace(referer, "%2f", "/")
        referer = string.replace(referer, "%3f", "?")
        urltuple = urlparse(referer)
        return urltuple[1], urltuple[2], urltuple[4]


    def __get_search_engine(self, domain, qs):
        s = domain.split(".")
        if len(s) == 2:
            domain = s[0]
        if len(s) >= 3:
            if s[0] == 'www': domain = '.'.join(s[1:-1])
            else: domain = '.'.join(s[:-1])
        
        search_engine = SearchEngines.get(domain)
        if not search_engine:
            return None

        search_phrase = None
        search_keywords = []
        qs_dict = parse_qs(qs)

        qs_str = qs_dict.get(search_engine['param'])

        if qs_str:
            search_string = string.lower(qs_str[0])
            search_string = string.replace(search_string, "+", " ")
            exclude = []
            for term in self.exclude_search_terms:
                if string.find(search_string, term) > -1:
                    exclude.append(term)

            if not exclude:
                search_phrase = search_string

            keywords = string.split(search_string)
            for keyword in keywords:
                keyword = string.strip(keyword)
                keyword = string.replace(keyword, '"', '')
                if keyword and keyword not in exclude:
                    search_keywords.append(keyword)
                    
        return search_engine, search_phrase, search_keywords
    

    def get_filename(self, month, year):
        return self.data_dir + os.sep + self.data_name + os.sep + \
               string.zfill(month, 2) + str(year)
            
        
    def output_pickle(self, filename):
        #?
        try:
            fp = open(filename, "w")
        except:
            print "Could not write file:", filename
            return

        p = pickle.Pickler(fp)
        p.dump(self.parsed_data)
        fp.close()

    def input_pickle(self, filename):
        #?
        try:
            fp = open(filename, "r")
        except:
            print "Could not read file:", filename
            return

        u = pickle.Unpickler(fp)
        self.parsed_data = u.load()
        fp.close()

    def ip_lookup(self, host):
        if self.__dns_cache.has_key(host): return self.__dns_cache.get(host)
        #print "HOST:", host
        #print "MATCH:", ip_address_re.match(host)
        if ip_address_re.match(host):
            # host is an ip address - lookup hostname
            ip_addr = host
            try:
                hostname = socket.gethostbyaddr(ip_addr)[0]
            except:
                hostname = ""
        else:
            # host is hostname - lookup ip address
            hostname = host
            try:
                ip_addr = socket.gethostbyname(hostname)
            except:
                ip_addr = ""

        self.__dns_cache[host] = (ip_addr, hostname)
        return ip_addr, hostname


    def get_last_date(self):
        return self.__last_date

#
#################################################
#

def usage():
    print
    print "Usage:"
    print sys.argv[0] + \
          " [ -c config | --config=config ] [--rebuild] [ -d x | --debug=x] [-V] [logfile1] [logfile2] [logfileN]"
    print
    sys.exit(0)


if __name__ == '__main__':    
    log_filenames = []
    config_file = "config"
    debug = 0
    rebuild=0
    noreport=0

    args = sys.argv[1:]
    try:
        (opts, getopts) = getopt.getopt(args, 'd:f:c:?hV',
                                        ["file=", "debug=", "noreport",
                                         "config=", "help", "rebuild"])
    except:
        print "\nInvalid command line option detected."
        usage()

    for opt, arg in opts:
        if opt in ('-h', '-?', '--help'):
            usage()
        if opt == '-V':
            print sys.argv[0], "- Scratchy - version", VERSION
            sys.exit(0)
        if opt == '-c':
            config_file = arg
        if opt == '--noreport':
            noreport = 1
        if opt in ('-d', '--debug'):
            try:
                debug = int(arg)
            except:
                print "debug value must be an integer"
                usage()            
        if opt in ('-f', '--file'):
            print """
Warning: the -f | --file command has been deprecated and may not work in future
releases.  Instead, append the file(s) you wish to parse at the end of the command
line."""
            log_filenames.append(arg)
        if opt == '--rebuild':
            rebuild = 1

    prefs = Prefs(config_file)
    filenames = getopts or log_filenames or prefs.get('ACCESS_LOG', 1)

    
    try:
        os.makedirs(os.path.join(prefs.get('DATA_DIR'), prefs.get('DATA_NAME')), 0700)
    except OSError, e: 
        if e.args[0] != 17: # 17 = directory exists (which we can ignore)
            print e
            sys.exit(0)
    except Exception, e:
        print e
        sys.exit(0)

    if not filenames:
        print ">> You must specify atleast 1 filename to parse"
        sys.exit(1)
        

    date_tuples = []
    for filename in filenames:
        # note: if using access_log* use double quotes around arg
        print ">> Parsing log:", filename
        log = Log(prefs, filename, rebuild)
        try:
            date_tuples += log.process_log()
        except Exception, e:
            print e

    unique = {}
    for date_tuple in date_tuples:
        unique[date_tuple] = 1
    date_tuples = unique.keys()

    log.compute_sessions(date_tuples)
    
    if not noreport:
        log.create_reports(date_tuples)


##    print "<pre>"
##    log.dump_stats()
##    print "</pre>"

    #last_date = log.get_last_date()
    #report.Report(last_date[0], last_date[1], config_file)





