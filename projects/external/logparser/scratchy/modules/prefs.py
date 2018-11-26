
import string, os, sys
from types import StringType, IntType

class Prefs:
    def __init__(self, filename="config"):
        self.__prefs = {}
        self.__set_defaults()
        self.read_prefs(filename)

    def __set_defaults(self):
        # all of these default prefs can be overridden in a config file
        # in the form of "OPTION_NAME: overridden value"
        self.__prefs = {'DATABASE': 'mysql',  # mysql or pysqlite
                        'TMP_FILE': "/tmp/scratchy.data",
                        
                        # pysqlite specific options
                        'SQLITE_DB': 'scratchydb',

                        # mysql specific options
                        'MYSQL_HOST': 'localhost',
                        'MYSQL_PORT': None,  # None = mysql default 3306
                        'MYSQL_USERNAME': 'scratchy',
                        'MYSQL_PASSWORD': 'itchy',
                        
                        ############################################
                        
                        'KNOWN_PAGES': ['html, cgi'],
                        'KNOWN_ALIASES': ['yourdomain,com', 'www.yourdomain.net'],
                        'VISIT_TIME': 3600,
                        'DATA_DIR': 'data',
                        'DATA_NAME': 'yourdata',
                        'ACCESS_LOG': '/var/log/apache/access_log',
                        'VERBOSE': 1,
                        'EXCLUDE_SEARCH_TERMS': [],
                        'EXCLUDE_URLS': [],
                        'EXCLUDE_HOSTNAMES': [],
                        
                        # COUNTRY_LOOKUP: enable (1) or disable (0) lookups
                        # of country codes from ip addresses.  Requires
                        # GeoIP C and Python API's available at:
                        # http://www.maxmind.com/app/geoip_country
                        'COUNTRY_LOOKUP': 1,
                        'GEOIP_DB': '/usr/local/share/GeoIP/GeoIP.dat',
                        
                        # Disables the ability to record and report a trace
                        # of each ip address accessing the site
                        'ENABLE_IP_TRACE': 0,
                        
                        # CHART_HEIGHT applies to some charts - currently
                        # daily, hourly and day of week are fixed since
                        # the labels are fixed.
                        'CHART_HEIGHT': 300,
                        'CHARSET_ENCODING': 'UTF-8',

                        ####################################################

                        # output formatters / data limits
                        'TIME_STR': '%m/%d/%y',
                        'TIME_DATE_STR': '%m/%d/%y %H:%M:%S',
                        'MAX_HOSTS': 25,
                        'MAX_PAGES': 25,
                        'MAX_FILES': 25,
                        #'MAX_DATES': 15,  # deprecated in 0.7.0
                        'MAX_FILE_TYPES': 10,
                        'MAX_STATUS_CODE': 10,
                        'MAX_ERROR_CODES': 5,
                        'MAX_ERROR_PAGES': 10,
                        'MAX_SEARCH_ENGINES': 10,
                        'MAX_SEARCH_STRINGS': 20,
                        'MAX_SEARCH_KEYWORDS': 20,
                        'MAX_EXTERNAL_LINKS': 20,
                        'MAX_OPERATING_SYSTEMS': 20,
                        'MAX_ROBOTS': 20,
                        'MAX_BROWSERS': 10,
                        'MAX_BROWSER_VERSIONS': 10,
                        'MAX_COUNTRIES': 15,

                        ###############################################

                        # background colors...
                        'COLOR_DEFAULT': '#ffffff',
                        'COLOR_HEADER': '#cccccc',
                        'COLOR_TITLE': '#666666',
                        'COLOR_HITS': '#3399FF',
                        'COLOR_PAGES': '#00CCFF',
                        'COLOR_VISIT_HEADER': "#FFFF66",
                        'COLOR_VISIT_NUMBER': "#FFFF99",
                        'COLOR_VISIT_FIRST': "#FFFF99",
                        'COLOR_VISIT_LAST': "#FFFF99",                      
                        'COLOR_BANDWIDTH': '#00CCCC',
                        'COLOR_SESSION_HEADER': '#FFCC66',
                        'COLOR_SESSION_MIN': '#FFCC33',
                        'COLOR_SESSION_MAX': '#FFCC33',
                        'COLOR_SESSION_AVG': '#FFCC33',
                        'COLOR_BROWSER': '#CCCC99',
                        'COLOR_MORE': '#eeeeee',
                        
                        ###############################################

                        # text colors
                        'COLOR_DEFAULT_TEXT': '#000000',
                        'COLOR_HEADER_TEXT': '#000000',
                        'COLOR_TITLE_TEXT': '#ffffff',
                        'COLOR_HITS_TEXT': '#000000',
                        'COLOR_PAGES_TEXT': '#000000',
                        'COLOR_VISIT_HEADER_TEXT': "#000000",
                        'COLOR_VISIT_NUMBER_TEXT': "#000000",
                        'COLOR_VISIT_FIRST_TEXT': "#000000",
                        'COLOR_VISIT_LAST_TEXT': "#000000",                      
                        'COLOR_BANDWIDTH_TEXT': '#000000',
                        'COLOR_SESSION_HEADER_TEXT': '#000000',
                        'COLOR_SESSION_MIN_TEXT': '#000000',
                        'COLOR_SESSION_MAX_TEXT': '#000000',
                        'COLOR_SESSION_AVG_TEXT': '#000000',
                        'COLOR_BROWSER_TEXT': '#000000',
                        'COLOR_MORE_TEXT': '#000000',
                        'COLOR_LINK_TEXT': '#006666',
                        'COLOR_LINK_VISITED_TEXT': '#006666',
                        'COLOR_LINK_HOVER_TEXT': '#000066',
                        'COLOR_CHART_ALT_BG': '#ffffe0',
                        
                        ###############################################
                        
                        # charts to create in reports (1 = yes, 0 = no)
                        'CHART_DAILY': 1,
                        'CHART_HOURLY': 1,
                        'CHART_DAY_OF_WEEK': 1,
                        'CHART_BROWSERS': 1,
                        'CHART_FILE_TYPES': 1,
                        'CHART_OPERATING_SYSTEMS': 1,
                        'CHART_COUNTRIES': 1,

                        ###############################################
                        
                        # templates to use for reports
                        'TEMPLATE_SUMMARY': os.path.join('misc', 'template_summary'),
                        'TEMPLATE_REPORT': os.path.join('misc', 'template_report'),
                        
                        # sort tables/charts by hits, pages or bandwidth
                        # Note: not all tables contain all 3 categories.
                        # daily, hourly and day of week tables are not sortable since they
                        # are displayed in sequential order (sun, mon, tues, etc...)
                        'SORT_FILE_TYPES': 'hits',
                        'SORT_COUNTRIES': 'hits',
                        'SORT_PAGES': 'hits',
                        'SORT_FILES': 'hits',
                        'SORT_HOSTS': 'hits',
                        'SORT_HTTP_STATUS': 'hits',
                        }

    def output_defaults(self):
        keys = self.__prefs.keys()
        keys.sort()

        for key in keys:
            val = self.__prefs[key]
            
            if type(val) == IntType:
                desc = "Integer"
            elif type(val) == StringType:
                if string.find(val, ",") != -1: desc = "Comma separated strings"
                else: desc = "String"
                            
            print "<tr>"
            print "   <td><a href=#%s>%s</a></td>" % (key, key)
            print "   <td>%s</td>" % desc
            print "   <td>%s</td>" % val
            print "</tr>"

        print "\n\n"
        for key in keys:
            print "<A name=%s>" % key
            print "<h4>%s</h4>" % key
            print "\n<hr>"
            

    def read_prefs(self, filename):
        try:
            fp = open(filename, "r")
        except Exception, e:
            print "Error:", str(e)
            print "Exiting.  Either create config or specify an alternate file with the -c flag"
            sys.exit(0)
        
        while 1:
            line = fp.readline()
            if not line: break

            line = line[:-1]
            if not line or line[0] == '#': continue

            idx = string.find(line, ':')
            if idx <= 0: continue

            key = line[:idx]
            val = line[idx+1:]

            string.strip(val)
            
            try:
                vals = string.split(val, ",")
                if len(vals) == 1:
                    v = string.strip(vals[0])
                    try:
                        v = int(v)
                    except:
                        pass
                    self.__prefs[key] = v
                else:
                    self.__prefs[key] = []
                    for v in vals:
                        v = string.strip(v)
                        try:
                            v = int(v)
                        except:
                            pass
                        self.__prefs[key].append(v)
            except:
                #???
                continue

        fp.close()


    def get(self, key, getlist=0):
        val = self.__prefs.get(key, "")
        if key[:5] == 'SORT_':
            err = 0
            if key in ("SORT_PAGES", 'SORT_FILES', 'SORT_FILE_TYPES') \
                   and val not in ('hits', 'bandwidth'):
                err = 1
            elif val not in ('hits', 'bandwidth', 'pages'):
                err = 1
                
            if err:    
                print "Error parsing value for %s -- using 'hits'" % key
                val = 'hits'
                
            if val == 'bandwidth': val = 'bytes'
                
        if getlist and  type(val) == StringType:
            val = [val]
        return val
                
            

