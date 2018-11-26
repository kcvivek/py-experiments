#!/usr/bin/env python
import os
import sys
import string
import time
from calendar import monthrange
import types
from urlparse import urlparse
import getopt
from shutil import copyfile
from stat import * #S_ISDIR, ST_MODE
import glob
#
#
from modules.filetypes import get_filetype
from modules.statuscodes import get_statuscode
from modules.prefs import Prefs
from modules.common import *
from modules.version import VERSION
from modules.useragents import BROWSERS
from modules.dictcursor import DictCursor
import modules.db as db


try:
    import pychartdir
    HAS_CHARTDIRECTOR = 1
except:
    print "-" * 60
    print "Failed to import ChartDirector module.  Charts will not be rendered."
    print "You can always install the ChartDirector module and re-run the report later"
    print "Refer to http://scratchy.sourceforge.net for more information"
    print "-" * 60
    HAS_CHARTDIRECTOR = 0

if HAS_CHARTDIRECTOR:
    from modules.chart import Chart


LOGO_IMAGE = "scratchy-small.gif"

def dictToList(dict):
    keys = dict.keys()
    nkeys = len(keys)
    l = [None] * nkeys

    for i in range(nkeys):
        key = keys[i]
        newdict = dict[key]
        newdict['__key__'] = key
        l[i] = newdict

    return l

def listToDict(_list, key):
    dict = {}
    for row in _list:
        dict[row[key]] = row
    return dict


def sortDictBy(list, key):
    nlist = map(lambda x, key=key: (x[key], x), list)
    nlist.sort()
    return map(lambda (key, x): x, nlist)


def getSortedDictList(dict, sortkey, reverse=0):
    l = dictToList(dict)
    l = sortDictBy(l, sortkey)
    if reverse:
        l.reverse()
    return l
    


######################################################################################################

class Report:
    def __init__(self, month, year, prefs, cursor=None):
        self.month = month
        self.year = year

        self.days_in_month = monthrange(year, month)[1]
        self.begdate = long(time.mktime( (year, month, 1, 0,0,0,0,0,0) ))
        self.enddate = long(time.mktime( (year, month, self.days_in_month,
                                          23, 59, 0,0,0,0) ))

        self.prefs = prefs
        self.__sorted_data_dict = {}
        
        self.report_dir = get_reportdir(self.prefs, month, year)
        
        filename = get_filename(self.prefs, month, year)

        self.__verbose = self.prefs.get('VERBOSE')
        self.__color_bandwidth = self.prefs.get('COLOR_BANDWIDTH')
        self.__color_hits = self.prefs.get('COLOR_HITS')
        self.__color_pages = self.prefs.get('COLOR_PAGES')
        self.__color_title = self.prefs.get('COLOR_TITLE')
        self.__country_lookup = self.prefs.get('COUNTRY_LOOKUP')

        self.__make_report_dir()
        self.__copy_logo()

        if not cursor:
            self.__db = db.connect(self.prefs)
            database = prefs.get('DATABASE').lower()
            if database == 'gadfly':
                self.cursor = DictCursor(self.__db)
            else:
                self.cursor = self.__db.cursor()
        else:
            self.cursor = cursor
                
        self.__get_totals()
                              
        if HAS_CHARTDIRECTOR:
            self.chart = Chart(self.__color_hits,
                               self.__color_pages,
                               self.__color_bandwidth,
                               self.prefs.get('COLOR_DEFAULT'),
                               self.prefs.get('COLOR_CHART_ALT_BG'),
                               self.prefs.get('CHART_HEIGHT'),
                               self.report_dir,
                               self.__verbose)
            
        self.__create_CSS()

        excluded_urls = self.prefs.get("EXCLUDE_URLS", 1)
        self.__excluded_urls = "\n"
        for url in excluded_urls:
            self.__excluded_urls += "AND url not like '%%%s%%'\n" % url

        self.create_report()


    def __get_totals(self):
        # obtain the totals for hits, pages and bytes for this month
        # and set the appropriate instance variables
        totals = db.select_totals(self.cursor,
                                  self.begdate,
                                  self.enddate)
        

        self.total_hits = int(totals['hits'] or 0)
        self.total_pages = int(totals['pages'] or 0)
        self.total_bytes = totals['bytes' or 0]


    def create_charts(self):
        # create the charts
        #print self.__sorted_data_dict.keys()
        
        if self.prefs.get('CHART_HOURLY'):
            self.chart.create_hourly_chart(self.__sorted_data_dict['hour']['data'])


        if self.prefs.get('CHART_DAY_OF_WEEK'):            
            self.chart.create_day_of_week_chart(self.__sorted_data_dict['day_of_week']['data'])

        if self.prefs.get('CHART_DAILY'):
            self.chart.create_daily_chart(self.__sorted_data_dict['day_of_month']['data'])


        if self.prefs.get('CHART_OPERATING_SYSTEMS'):
            data = self.__sorted_data_dict['op_sys']['data']
            more = self.__sorted_data_dict['op_sys']['more']

            self.chart.create_sorted_chart("opsys.png",
                                           "Operating Systems",
                                           "op_sys",
                                           "Operating System",
                                           "Hits",
                                           data,
                                           'hits',
                                           more)


        if self.prefs.get('CHART_FILE_TYPES'):
            data = self.__sorted_data_dict['file_type']['data']
            more = self.__sorted_data_dict['file_type']['more']

            self.chart.create_sorted_chart("file_types.png",
                                           "File Types",
                                           "file_type",
                                           "File Type",
                                           "Hits, Bandwidth(kb)",
                                           data,
                                           ("hits", "bytes"),
                                           more)



        if self.prefs.get('CHART_BROWSERS'):
            data = self.__sorted_data_dict['browser']['data']
            more = self.__sorted_data_dict['browser']['more']
            
            self.chart.create_sorted_chart("browser.png",
                                           "Browsers",
                                           "browser",
                                           "Browser",
                                           "Hits",
                                           data,
                                           'hits',
                                           more)
            


        if self.prefs.get('CHART_COUNTRIES') and self.__country_lookup:
            data = self.__sorted_data_dict['country']['data']
            more = self.__sorted_data_dict['country']['more']

            self.chart.create_sorted_chart("country.png",
                                           "Countries",
                                           "country",
                                           "Country",
                                           "Hits, Pages, Bandwidth (kb)",
                                           data,
                                           ('pages', 'hits', 'bytes'),
                                           more)


    def __add_chart_images(self, html):
        # replace chart tags with the chart image or empty string (if
        # charts are disabled).
        charts = [ ("day_of_week.png", '%% BY_DAY_CHART %%', 'DAY_OF_WEEK'),
                   ('hourly.png', '%% BY_HOUR_CHART %%', 'HOURLY'),
                   ('daily.png', '%% DAILY_LOG_CHART %%', 'DAILY'),
                   ('opsys.png', '%% OPERATING_SYSTEMS_CHART %%', 'OPERATING_SYSTEMS'),
                   ('file_types.png', '%% FILE_TYPES_CHART %%', 'FILE_TYPES'),
                   ('browser.png', '%% BROWSER_VERSION_CHART %%', 'BROWSERS'),
                   ('country.png', '%% COUNTRY_CHART %%', 'COUNTRIES'),
                   ]

        for chart in charts:
            if HAS_CHARTDIRECTOR and self.prefs.get('CHART_%s' % chart[2]):
                subst = "<IMG SRC=%s>" %  chart[0]
            else:
                subst = ""
            html = string.replace(html, chart[1], subst)

        return html
            

    def __make_report_dir(self):
        try:
            os.makedirs(self.report_dir, 0700)
        except OSError, e:
            if e.args[0] != 17: # 17 = directory exists (which we can ignore)
                print e
                sys.exit(0)
        except Exception, e:
            print e
            sys.exit(0)
        

    def __copy_logo(self):
        try:
            copyfile(os.path.join("misc", LOGO_IMAGE),
                     os.path.join(self.prefs.get('REPORT_DIR'), LOGO_IMAGE))
        except Exception, e:
            print "Error copying logo file:", str(e)
            

    def __get_scratchy_link(self, relpath="../../"):
        ahref = '<a href=http://scratchy.sourceforge.net target=x>'

        html = "<p><hr>"
        html += '%s<img alt="" border=0 src=%s%s></a>' % (ahref, relpath, LOGO_IMAGE)
        html += "<font size=-1>This report produced by %sScratchy</a> - an Apache access log parser and reporter</font>" % ahref

        return html
    

    def __create_CSS(self, path=None):
        html = ""
        html += '<STYLE TYPE="text/css">\n<!--\n'

        html += """A { font: 10px helvetica, sans-serif; }
        A:link    { color: %s; text-decoration: none; }
        A:visited { color: %s; text-decoration: none; }
        A:hover   { color: %s; text-decoration: underline; }
        """ % (self.prefs.get('COLOR_LINK_TEXT'),
               self.prefs.get('COLOR_LINK_VISITED_TEXT'),
               self.prefs.get('COLOR_LINK_HOVER_TEXT'))

        html += '.TDNORM { font: 12px helvetica, sans-serif; background-color: %s; margin-top: 0 }\n' % self.prefs.get('COLOR_DEFAULT')
            
        html += '.TDHITS { font: 12px helvetica, sans-serif; background-color: %s; text-color: %s margin-top: 0 }\n' % (self.prefs.get('COLOR_HITS'), self.prefs.get('COLOR_HITS_TEXT'))
        
        html += '.TDKB { font: 12px helvetica, sans-serif; background-color: %s; text-color: %s margin-top: 0 }\n' % (self.prefs.get('COLOR_BANDWIDTH'), self.prefs.get('COLOR_BANDWIDTH_TEXT'))
        html += '.TDPAGES { font: 12px helvetica, sans-serif; background-color: %s; text-color: %s margin-top: 0 }\n' % (self.prefs.get('COLOR_PAGES'), self.prefs.get('COLOR_PAGES_TEXT'))


        html += '.TABLEX { background-color: %s; padding: 2px 2px 2px 2px; margin-top: 0 }\n' % self.prefs.get('COLOR_DEFAULT')
            
        html += ".TDX { font: 12px helvetica, sans-serif; text-align:center; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_TITLE_TEXT'), self.prefs.get('COLOR_TITLE'))
        
        html += ".TDHEADER { font: 12px helvetica, sans-serif; text-align:center; color: %s; background-color: %s}\n" %( self.prefs.get('COLOR_HEADER_TEXT'),  self.prefs.get('COLOR_HEADER'))
        
        html += ".TDVISITHEADER { font: 12px helvetica, sans-serif; text-align:center; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_VISIT_HEADER_TEXT'), self.prefs.get('COLOR_VISIT_HEADER'))
        
        html += ".TDSESSIONHEADER { font: 12px helvetica, sans-serif; text-align:center; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_SESSION_HEADER_TEXT'), self.prefs.get('COLOR_SESSION_HEADER'))

        html += ".TDLEFT { font: 12px helvetica, sans-serif; text-align:left; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_DEFAULT_TEXT'), self.prefs.get('COLOR_DEFAULT'))

            
        html += ".TDRIGHT { font: 12px helvetica, sans-serif; text-align:right; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_DEFAULT_TEXT'), self.prefs.get('COLOR_DEFAULT'))

            
        html += ".TDMORELEFT { font: 12px helvetica, sans-serif; text-align:left; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_MORE_TEXT'), self.prefs.get('COLOR_MORE'))
            
        html += ".TDMORERIGHT { font: 12px helvetica, sans-serif; text-align:right; color: #000000; background-color: %s}\n" % self.prefs.get('COLOR_MORE')            

        html += ".TDFONT { font: 12px helvetica, sans-serif; text-align:center; color: %s}\n" % self.prefs.get('COLOR_DEFAULT_TEXT')
            
        html += ".TDBROWSER_LEFT { font: 12px helvetica, sans-serif; text-align:left; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_BROWSER_TEXT'), self.prefs.get('COLOR_BROWSER'))
            
        html += ".TDBROWSER_RIGHT { font: 12px helvetica, sans-serif; text-align:right; color: %s; background-color: %s}\n" % (self.prefs.get('COLOR_BROWSER_TEXT'), self.prefs.get('COLOR_BROWSER'))
            
        html += "//-->\n</STYLE>\n"
        self.css_name = self.prefs.get("DATA_NAME") + ".css"
        self.save_report(html, self.css_name, path)


    def create_report(self):
        print ">> Creating report for: %d/%d" % (self.month, self.year)

        html = "<html>\n<head>\n"
        html += '<meta http-equiv="Content-Type" content="text/html; charset=%s">\n' % self.prefs.get('CHARSET_ENCODING')
        html += "<title>Scratchy - %s - %d/%d</title>\n" % (self.prefs.get('DATA_NAME'), self.month, self.year)

        html += '<link href="%s" type="text/css" rel="stylesheet">' % self.css_name
       
        html += "</head>\n"
        html += "<body bgcolor=%s>\n" % self.prefs.get('COLOR_DEFAULT')

        html += self.get_template(self.prefs.get('TEMPLATE_REPORT'))


        #### output each table ####
        table = self.__get_pages_table(self.prefs.get('MAX_PAGES'))
        html = html.replace("%% PAGES_TABLE %%", table)

        table = self.__get_files_table(self.prefs.get('MAX_FILES'))
        html = html.replace("%% FILES_TABLE %%", table)        

        table = self.__get_hosts_table(self.prefs.get('MAX_HOSTS'))
        html = html.replace("%% HOSTS_TABLE %%", table)

        table = self.__get_file_types_table(self.prefs.get('MAX_FILE_TYPES'))
        html = html.replace("%% FILE_TYPES_TABLE %%", table)

        
        table = self.__get_status_codes_table(self.prefs.get('MAX_STATUS_CODE'))
        html = html.replace("%% STATUS_CODES_TABLE %%", table)
        
        table = self.__get_errors_table(self.prefs.get('MAX_ERROR_CODES'),
                                        self.prefs.get('MAX_ERROR_PAGES'))
        html = html.replace("%% ERRORS_TABLE %%", table)
        
        table = self.__get_daily_table()
        html = html.replace("%% DAILY_LOG_TABLE %%", table)

        table = self.__get_hourly_table()
        html = html.replace("%% BY_HOUR_TABLE %%", table)
        
        table = self.__get_day_of_week_table()
        html = html.replace("%% BY_DAY_TABLE %%", table)

        table = self.__get_access_method_table()
        html = html.replace("%% ACCESS_METHOD_TABLE %%", table)
        
        addl_where = " AND referer_domain NOT IN (%s) " % \
                     db.get_referer_domain_clause(["-"] + \
                                                  self.prefs.get('KNOWN_ALIASES', 1))
        table = self.__get_generic_table("External Link",
                                         'referer_domain',
                                         'referer_domain',
                                         self.prefs.get('MAX_EXTERNAL_LINKS'),
                                         addl_where_crit=addl_where)
        html = html.replace("%% EXTERNAL_LINKS_TABLE %%", table)

        table = self.__get_generic_table("Search Engine",
                                         'search_engine',
                                         'search_engine',
                                         self.prefs.get('MAX_SEARCH_ENGINES'))
        html = html.replace("%% SEARCH_ENGINES_TABLE %%", table)

        table = self.__get_generic_table("Search Strings",
                                         'search_string',
                                         'search_string',
                                         self.prefs.get('MAX_SEARCH_STRINGS'))
        html = html.replace("%% SEARCH_PHRASES_TABLE %%", table)

        table = self.__get_search_keyword_table("Search Keywords",
                                         self.prefs.get('MAX_SEARCH_KEYWORDS'))
        html = html.replace("%% SEARCH_KEYWORDS_TABLE %%", table)

        table = self.__get_generic_table("Operating System",
                                         "op_sys",
                                         "op_sys",
                                         self.prefs.get('MAX_OPERATING_SYSTEMS'))
        html = html.replace("%% OPERATING_SYSTEMS_TABLE %%", table)

        table = self.__get_generic_table("Robot",
                                         'robot',
                                         'robot',
                                         self.prefs.get('MAX_ROBOTS'))
        html = html.replace("%% ROBOTS_TABLE %%", table)

        if self.__country_lookup:
            table = self.__get_country_table(self.prefs.get('MAX_COUNTRIES'))
        else:
            table = ""
            
        html = html.replace("%% COUNTRY_TABLE %%", table)

        table = self.__get_browser_version_table(self.prefs.get('MAX_BROWSERS'),
                                                 self.prefs.get('MAX_BROWSER_VERSIONS'))
        html = html.replace("%% BROWSER_VERSION_TABLE %%", table)

        table = self.__get_summary_table()
        html = html.replace("%% SUMMARY_TABLE %%", table)
        
        date = MONTHS.get(self.month) + ", " + str(self.year)
        html = html.replace("%% REPORT_DATE %%", date)
        html = html.replace("%% REPORT_NAME %%", self.prefs.get('DATA_NAME'))

        html += self.__get_scratchy_link()

        html = self.__add_chart_images(html)
        
        self.save_report(html, "index.html")
        self.create_charts()
        #print self.__sorted_data_dict['Hour']
        

    def create_ip_trace_page(self, ip_addr, ip_addr_id):
        try:
            html = "<html>\n<head>\n"
            html += '<meta http-equiv="Content-Type" content="text/html; charset=%s">\n' % self.prefs.get('CHARSET_ENCODING')
            html += "<title>Log Analysis</title>\n"
            html += '<link href="%s" type="text/css" rel="stylesheet">' % self.css_name

            html += "<center><table>"
            html += self.__title_row("Page", 1,
                                     ("<td CLASS=TDHEADER>Time</td>",
                                      "<td CLASS=TDHEADER>Referer</td>"))

            tmstr = self.prefs.get('TIME_DATE_STR')
            urls = db.select_ip_trace(self.cursor,
                                      ip_addr_id,
                                      self.begdate,
                                      self.enddate)
                                      
            for url in urls:
                ref = url.get('referer_domain', "")
                if ref in self.prefs.get('KNOWN_ALIASES', 1):
                    ref = ""
#                if ref:
#                    ref = urlparse(ref)[1]

                
                html += self.__data_row(url['url'],
                                        time.strftime(tmstr, time.localtime(url['timestamp'])),
                                        ref)
                                        

            html += "</table></center></html>"
            self.save_report(html, ip_addr + ".html")
            return 1
        except:
            return 0
        

    def get_template(self, filename):
        fp = open(filename)
        html = fp.read()
        fp.close()
        return html
        

    def save_report(self, html, fname, otherPath=None):
        filename = os.path.join(otherPath or self.report_dir, fname)
        
        if self.__verbose: print ">> Creating file:", filename
        
        try:
            fp = open(filename, "w")
        except Exception, e:
            print "Error opening report file", str(e)

        fp.write("%s\n" % html)
        fp.close()


    def get_pct(self, num, den):
        try:
            pct = float(num) / float(den) * 100.0
            pct_str = "%.2f" % pct
            pct = float(pct_str)
        except:
            pct = 0
            
        return pct

    
    def __more_row(self, num, cols, more, indent=0):
        html = "<tr>"

        if type(cols) is types.StringType:
            cols = [cols]
            
        for i in range(indent):
            html += "<td class=TDNORM>&nbsp;</td>"
            
        html += "<td class=TDMORELEFT>&nbsp;%s more&nbsp;</td>" % format_number(num)

        for col in cols:
            if col == "":
                html += "<td class=TDMORERIGHT>&nbsp</td>\n"
            else:
                if col == 'bytes':
                    val = get_kb(more[col])
                else:
                    val = int(more[col])
                    
                html += "<td class=TDMORERIGHT>&nbsp;%s&nbsp;</td>\n" % format_number(val)

        html += "</tr>\n"
        return html
    

    def __data_row(self, *args):
        html = "<tr>"
        for arg in args:
            atype = type(arg)
            if atype in (types.IntType, types.FloatType, types.LongType):
                align = "TDRIGHT"
                arg = format_number(arg)
            else:
                align = "TDLEFT"
            html += "   <td class=%s>&nbsp;%s&nbsp;</td>\n" % (align, arg)

        html += "</tr>\n"
        return html


    def __title_row(self, title, colspan=1, cols=('hits', 'pages', 'bandwidth')):
        html = "<td CLASS=TDHEADER colspan=%d>%s</td>\n" % (colspan, title)

        for col in cols:
            if col == 'hits':
                html += "<td class=TDHITS>Hits</td>\n"
            elif col == 'pages':
                html += "<td class=TDPAGES>Pages</td>\n"
            elif col == 'bandwidth':
                html += "<td class=TDKB>Bandwidth (Kb)</td>\n"
            else:
                html += "%s\n" % col
        return html
    

    def __get_files_table(self, num=0):
        html = "<table>"
        html += self.__title_row("Files", 1, ('hits', 'bandwidth'))

        sorted, more = db.select_joined_stats(self.cursor,
                                              "url",
                                              "url",
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('SORT_FILES'),
                                              'DESC',
                                              addl_where_crit=self.__excluded_urls)

        count = len(sorted)
        for i in range(count):
            page = sorted[i]
            html += self.__data_row(page['url'],
                                    page['hits'],
                                    get_kb(page['bytes']))

        if more:
            html += self.__more_row(more['count'], ('hits', 'bytes'), more)
            
        html += "</table>"
        return html


    def __get_pages_table(self, num=0):
        html = "<table>"
        html += self.__title_row("Pages", 1, ('hits', 'bandwidth'))


        sorted, more = db.select_joined_stats(self.cursor,
                                              "url",
                                              "url",
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('SORT_PAGES'),
                                              'DESC',
                                              1,
                                              self.__excluded_urls)
        
        totalnum = len(sorted)
        for i in range(totalnum):
            page = sorted[i]
            
            html += self.__data_row(page['url'],
                                    page['hits'],
                                    get_kb(page['bytes']))

        html += "</table>"
        return html



    def __get_hosts_table(self, num=0):
        html = "<table>"

        html += """
        <tr>
        <td class=TDHEADER colspan=5>&nbsp;</td>
        <td class=TDVISITHEADER colspan=3>Visits</td>
        <td class=TDSESSIONHEADER colspan=3>Sessions</td>
        </tr>
        """
        
        html += self.__title_row("Hosts", 2,
                                 ('hits', 'pages', 'bandwidth',
                                  "<td class=TDFONT bgcolor=%s>Number</td>" % (self.prefs.get('COLOR_VISIT_NUMBER')),
                                  "<td class=TDFONT bgcolor=%s>First</td>" % (self.prefs.get('COLOR_VISIT_FIRST')),
                                  "<td class=TDFONT bgcolor=%s>Last</td>" % (self.prefs.get('COLOR_VISIT_LAST')),
                                  "<td class=TDFONT bgcolor=%s>Min</td>" % (self.prefs.get('COLOR_SESSION_MIN')),
                                  "<td class=TDFONT bgcolor=%s>Max</td>" % (self.prefs.get('COLOR_SESSION_MAX')),
                                  "<td class=TDFONT bgcolor=%s>Avg</td>" % (self.prefs.get('COLOR_SESSION_AVG')) ))

        ip_trace_enabled = self.prefs.get('ENABLE_IP_TRACE')


        excluded_hostnames = self.prefs.get("EXCLUDE_HOSTNAMES", 1)
        excluded = ""
        if excluded_hostnames:
            excluded_hostnames = ["'%s'" % h for h in excluded_hostnames]
            joined = ','.join(excluded_hostnames)
            if joined:
                excluded = "\n    AND hostname not in (%s)" % joined

        sorted, more = db.select_joined_stats(self.cursor,
                                              "ip_addr",
                                              ("ip_addr", "hostname", "ip_addr.ip_addr_id"),
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('SORT_HOSTS'),
                                              'DESC',
                                              addl_where_crit=excluded)

        count = get_range(sorted, num)
        hostname = ""
        
        for i in range(count):
            host = sorted[i]

            key = host['ip_addr']
            ip_addr_id = host.get('ip_addr_id') or host.get("ip_addr.ip_addr_id")
            session = db.select_session_stats(self.cursor,
                                              ip_addr_id,
                                              self.begdate,
                                              self.enddate)


            ip_addr = key
            if ip_trace_enabled and      \
               host['pages'] and         \
               self.create_ip_trace_page(key, ip_addr_id):
                ip_addr = '<a href="%s.html">%s</a>' % (key, key)

            html += self.__data_row(ip_addr,
                                    host.get('hostname'),
                                    host['hits'],
                                    int(host['pages']),
                                    get_kb(host['bytes']),
                                    session.get('num', 0),
                                    self.__get_time_str(session.get('first', 0)),
                                    self.__get_time_str(session.get('last', 0)),
                                    session.get('duration_min'),
                                    session.get('duration_max'),
                                    float("%.1f" % \
                                          (float(session.get('duration_avg', "0")) or
                                           0.0)))

        html += self.__get_more_summary(sorted, count, ("", "hits", "pages", "bytes"))

        html += "</table>"
        return html



    def __get_errors_table(self, cnum=0, pnum=0):
        html = "<table>"
        html += self.__title_row("Code", 1,
                                 ("<td class=TDHEADER>Error</td>",
                                  "<td class=TDHEADER>Page</td>",
                                  'hits'))

        csorted, cmore = db.select_log_stats_list(self.cursor,
                                                  'status_code',
                                                  self.begdate,
                                                  self.enddate,
                                                  cnum or None,
                                                  'hits',
                                                  'DESC',
                                                  "status_code >= 400")

        ccount = get_range(csorted, cnum)
        for i in range(ccount):
            code = csorted[i]['status_code']
            chits = csorted[i]['hits']

            html += "<tr>"
            html += "<td class=TDBROWSER_LEFT>%s</td>" % code
            html += "<td class=TDBROWSER_LEFT>%s</td>" % get_statuscode(code)
            html += "<td class=TDBROWSER_LEFT>&nbsp;</td>"
            html += "<td class=TDBROWSER_RIGHT>%s&nbsp;</td>" % chits 
            html += "</tr>"
            
            psorted, pmore = db.select_error_urls(self.cursor,
                                                  code,
                                                  pnum or None,
                                                  self.begdate,
                                                  self.enddate)
            r = get_range(psorted, pnum)

            for i in range(r):
                row = psorted[i]
                html += self.__data_row("",
                                        "",
                                        row['url'],
                                        row['hits'])
            if pmore:
                html += self.__more_row(pmore['count'], "hits", pmore, 2)

        if cmore:
            html += self.__more_row(cmore['count'], ("", "","hits"), cmore)
        html += "</table>"
        return html    



    def __get_daily_table(self):
        html = "<table>"

        html += self.__title_row("Date", 1, ('hits', 'pages', 'bandwidth',
                                             "<td rowspan=16>&nbsp;&nbsp;&nbsp;</td>",
                                             "<td class=TDHEADER>Date</td>",
                                             'hits', 'pages', 'bandwidth'))


        sdict = db.select_log_stats_dict(self.cursor,
                                         'day_of_month',
                                         self.begdate,
                                         self.enddate)

        sorted = []
        for i in range(1, self.days_in_month + 1):
            d = sdict.get(i, {'hits': 0L, 'bytes': 0L, 'pages': 0L})
            d['day_of_month'] = i
            sorted.append(d)
        
        self.__sorted_data_dict['day_of_month'] = {'data': sorted}

        div, mod = divmod(self.days_in_month, 2)
        count = div + mod

        label = MONTHS.get(self.month)[:3]

        for i in range(count):
            day1 = sorted[i]
            col2 = i + count

            try:
                day2 = sorted[col2]
                html += self.__data_row("%s %d" % (label, i+1),
                                        day1['hits'],
                                        int(day1['pages']),
                                        get_kb(day1['bytes']),
                                        "%s %d" % (label, col2+1),
                                        day2['hits'],
                                        int(day2['pages']),
                                        get_kb(day2['bytes']))
            except:
                html += self.__data_row("%s %d" % (label, i+1),
                                        day1['hits'],
                                        int(day1['pages']),
                                        get_kb(day1['bytes']),
                                        "&nbsp;",
                                        "&nbsp;",
                                        "&nbsp;",
                                        "&nbsp;")


        html += "</table>"
        return html


    def __get_hourly_table(self):
        html = "<table>"

        dict = db.select_log_stats_dict(self.cursor,
                                        'hour',
                                        self.begdate,
                                        self.enddate)

        self.__sorted_data_dict['hour'] = {'data': dict}

        html += self.__title_row("Hour", 1, ('hits', 'pages', 'bandwidth',
                                             "<td rowspan=13>&nbsp;&nbsp;&nbsp;</td>",
                                             "<td class=TDHEADER>Hour</td>",
                                             'hits', 'pages', 'bandwidth'))

        for i in range(12):
            hour1 = dict.get(i, {'hits': 0, 'pages': 0, 'bytes':0})
            hour2 = dict.get(i+12, {'hits': 0, 'pages': 0, 'bytes':0})

            if i == 0:
                am = "12 AM"
                pm = "12 PM"
            else:
                am = string.zfill(i, 2) + " AM"
                pm = string.zfill(i, 2) + " PM"

            html += self.__data_row(am,
                                    hour1['hits'],
                                    int(hour1['pages']),
                                    get_kb(hour1['bytes']),
                                    pm,
                                    hour2['hits'],
                                    int(hour2['pages']),
                                    get_kb(hour2['bytes']))
                                                           

        html += "</table>"
        return html


    def __get_day_of_week_table(self):
        html = "<table>"
        html += self.__title_row("Day of Week")

        dict = db.select_log_stats_dict(self.cursor,
                                        'day_of_week',
                                        self.begdate,
                                        self.enddate)

        self.__sorted_data_dict['day_of_week'] = {'data': dict}
        
        for i in (6,0,1,2,3,4,5):
            day = dict.get(i, {'hits': 0, 'pages': 0, 'bytes':0})
            html += self.__data_row(DAYS[i],
                                    day['hits'],
                                    day['pages'],
                                    get_kb(day['bytes']))
                                                               
        html += "</table>"
        return html



    def __get_country_table(self, num=0):
        if not self.__country_lookup: return ""
        html = "<table>"
        html += self.__title_row("Countries")

        sorted, more = db.select_joined_stats(self.cursor,
                                              "country",
                                              "country",
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('SORT_COUNTRIES'),
                                              'DESC')
        
        self.__sorted_data_dict['country'] = {'data': sorted,
                                              'more': more}

        count = len(sorted)
        for i in range(count):
            row = sorted[i]
            html += self.__data_row(row['country'],
                                    row['hits'],
                                    int(row['pages']),
                                    get_kb(row['bytes']))

        if more:
            html += self.__more_row(more['count'],
                                    ("hits", 'pages', "bytes"),
                                    more)

        html += "</table>"
        return html


    def __get_file_types_table(self, num=0):
        html = "<table>"
        html += self.__title_row("File type", 2, ('hits',
                                                  '<td class=TDHITS>Pct.</td>',
                                                  'bandwidth'))

        sorted, more = db.select_joined_stats(self.cursor,
                                              "file_type",
                                              "file_type",
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('SORT_FILE_TYPES'),
                                              'DESC')


        self.__sorted_data_dict['file_type'] = {'data': sorted,
                                                'more': more}
        
        count = len(sorted)
        for i in range(count):
            filetype = sorted[i]
            html += self.__data_row(filetype['file_type'],
                                    get_filetype(filetype['file_type']),
                                    filetype['hits'],
                                    self.get_pct(filetype['hits'], self.total_hits),
                                    get_kb(filetype['bytes']))

        if more:
            other_hits = more['hits']
            more['pct'] = self.get_pct(other_hits, self.total_hits)
            cols = ("", "hits", "pct", "bytes")
            html += self.__more_row(more['count'], cols, more)

        html += "</table>"
        return html


    def __get_summary_table(self):
        html = "<table>"
        html += self.__title_row("Summary", 1)

        label = MONTHS.get(self.month) + ", " + str(self.year)
        html += self.__data_row(label,
                                self.total_hits,
                                self.total_pages,
                                get_kb(self.total_bytes))
        
        html += "</table>"
        return html
    

    def __get_status_codes_table(self, num=0):
        html = "<table>"
        html += self.__title_row("Status Codes", 2)

        sorted, more = db.select_log_stats_list(self.cursor,
                                                'status_code',
                                                self.begdate,
                                                self.enddate,
                                                self.prefs.get('MAX_STATUS_CODE'),
                                                self.prefs.get('SORT_HTTP_STATUS'),
                                                )

        count = len(sorted)
        for i in range(count):
            code = sorted[i]
            html += self.__data_row(code['status_code'],
                                    get_statuscode(code['status_code']),
                                    code['hits'],
                                    int(code['pages']),
                                    get_kb(code['bytes']))

        if more:
            html += self.__more_row(more['count'], ('', 'hits', 'pages', 'bytes'), more)

            
        html += "</table>"
        return html



    def __get_generic_table(self, title, table, col, num=0,
                            sort='hits', order='DESC',
                            addl_where_crit=None):
        html = "<table>"
        html += self.__title_row(title, 1)

        sorted, more = db.select_joined_stats(self.cursor,
                                              table,
                                              col,
                                              num or None,
                                              self.begdate,
                                              self.enddate,
                                              sort,
                                              order,
                                              0,
                                              addl_where_crit)

        self.__sorted_data_dict[col] = {'data': sorted,
                                        'more': more}

        count = len(sorted)
        for i in range(count):
            row = sorted[i]
            if row[col] == '': continue
            html += self.__data_row(row[col],
                                    row['hits'],
                                    int(row['pages']),
                                    get_kb(row['bytes']))

        if more:
            html += self.__more_row(more['count'],
                                    ('hits', 'pages', 'bytes'),
                                    more)
            
        html += "</table>"
        return html


    def __get_search_keyword_table(self, title, num=0,
                            sort='hits', order='DESC'):
        html = "<table>"
        html += self.__title_row(title, 1)

        sorted, more = db.select_search_keywords(self.cursor,
                                                 num or None,
                                                 self.begdate,
                                                 self.enddate,
                                                 sort,
                                                 order)
        count = len(sorted)
        for i in range(count):
            row = sorted[i]

            #if row[col] == '': continue
            sk = row.get('search_keyword') or row.get('SK.search_keyword')
            html += self.__data_row(sk, 
                                    row['hits'],
                                    int(row['pages']),
                                    get_kb(row['bytes']))

        if more:
            html += self.__more_row(more['count'],
                                    ('hits', 'pages', 'bytes'),
                                    more)
            
        html += "</table>"
        return html    


    def __get_browser_version_table(self, bnum=0, vnum=0):
        html = "<table>"
        html += self.__title_row("Browser Name",
                                 1,
                                 ("<td class=TDHEADER>Version</td>",
                                  'hits',
                                  '<td class=TDHITS>Type Pct.</td>',
                                  '<td class=TDHITS>Overall Pct.</td>'))

        bsorted, more = db.select_joined_stats(self.cursor,
                                               "browser",
                                               "browser",
                                               self.prefs.get('MAX_BROWSERS'),
                                               self.begdate,
                                               self.enddate,
                                               addl_where_crit=' AND browser.browser_id != 0')

        self.__sorted_data_dict['browser'] = {'data': bsorted,
                                              'more': more}


        totals = db.select_browser_totals(self.cursor,
                                          self.begdate,
                                          self.enddate)
        total_bhits = totals['hits']

        versions = db.select_browser_versions(self.cursor,
                                              self.begdate,
                                              self.enddate,
                                              self.prefs.get('MAX_BROWSER_VERSIONS')
                                              )

        bcount = len(bsorted)
        for i in range(bcount):
            browser = bsorted[i]['browser']
            bhits = bsorted[i]['hits']

            html += "<tr>"
            html += "<td class=TDBROWSER_LEFT>%s</td>" % BROWSERS.get(browser,
                                                                      browser)
            html += "<td class=TDBROWSER_LEFT>&nbsp;</td>"
            html += "<td class=TDBROWSER_RIGHT>%s&nbsp;</td>" % bhits 
            html += "<td class=TDBROWSER_RIGHT colspan=2>%s&nbsp;</td>" % self.get_pct(bhits, total_bhits)
            html += "</tr>"

            #vers = versions.get(browser)
            versions, vmore = \
                      db.select_browser_versions(self.cursor,
                                                 browser,
                                                 self.begdate,
                                                 self.enddate,
                                                 self.prefs.get('MAX_BROWSER_VERSIONS')
                                                 )

            if versions:
                for vers in versions:
                    html += self.__data_row("",
                                            vers['version'],
                                            vers['hits'],
                                            self.get_pct(vers['hits'], bhits),
                                            self.get_pct(vers['hits'], total_bhits))
                if vmore:
                    other_hits = vmore['hits']
                    vmore['pct1'] = self.get_pct(other_hits, bhits)
                    vmore['pct2'] = self.get_pct(other_hits, total_bhits)
                    cols = ("hits", "pct1", "pct2")
                    html += self.__more_row(vmore['count'], cols, vmore, 1)


                    
##            if vers:
##                r = len(vers)
##                for i in range(r):
##                    row = vers[i]
##                    print row, "\n"
##                    if not row.has_key('count'):
##                        html += self.__data_row("",
##                                                row['version'],
##                                                row['hits'],
##                                                self.get_pct(row['hits'], bhits),
##                                                self.get_pct(row['hits'], total_bhits))
##                    else:
##                        other_hits = row['hits']
##                        row['pct1'] = self.get_pct(other_hits, bhits)
##                        row['pct2'] = self.get_pct(other_hits, total_bhits)
##                        cols = ("hits", "pct1", "pct2")
##                        html += self.__more_row(row['count'], cols, row, 1)

        if more:
            other_hits = more['hits']
            more['pct'] = self.get_pct(other_hits, total_bhits)
            cols = ("", "hits", "", "pct")
            html += self.__more_row(more['count'], cols, more)                    
        html += "</table>"
        return html    
                                         

    def __get_more_summary_dict(self, rows, start, cols):
        more = {}

        if len(rows) <= start:
            return more

        if type(cols) == types.StringType:
            cols = [cols]

        num = 0
        for i in range(start, len(rows)):
            num += 1
            for col in cols:
                try:
                    more[col] += rows[i][col]
                except:
                    more[col] = rows[i].get(col, 0)

        if num: more['__num__'] = num

        return more


    def __get_more_summary(self, rows, start, cols, indent=0):
        if len(rows) <= start:
            return ""

        more = {}

        if type(cols) == types.StringType:
            cols = [cols]

        num = 0
        for i in range(start, len(rows)):
            num += 1
            for col in cols:
                try:
                    more[col] += rows[i][col]
                except:
                    more[col] = rows[i].get(col, 0)

        if more: return self.__more_row(num, cols, more, indent)
        else: return ""
            



    def __get_access_method_table(self              ):
        html = "<table>"
        html += self.__title_row("Origin", 1, ('hits',
                                                '<td class=TDHITS>Pct.</td>',
                                               "pages",
                                               "bandwidth"))

        direct = db.select_access_method(self.cursor,
                                         "-",
                                         "IN",
                                         self.begdate,
                                         self.enddate)

        internal = db.select_access_method(self.cursor,
                                           self.prefs.get('KNOWN_ALIASES'),
                                           "IN",
                                           self.begdate,
                                           self.enddate)
        
        external = db.select_access_method(self.cursor,
                                           ["-"] + self.prefs.get('KNOWN_ALIASES', 1),
                                           "NOT IN",
                                           self.begdate,
                                           self.enddate)



        html += self.__data_row("Direct Access",
                                direct['hits'],
                                self.get_pct(direct['hits'], self.total_hits),
                                int(direct['pages']),
                                get_kb(direct['bytes']))


        html += self.__data_row("Internal Link",
                                internal['hits'],
                                self.get_pct(internal['hits'], self.total_hits),
                                int(internal['pages']),
                                get_kb(internal['bytes']))



        html += self.__data_row("External Link",
                                external['hits'],
                                self.get_pct(external['hits'], self.total_hits),
                                int(external['pages']),
                                get_kb(external['bytes']))


                                
        html += "</table>"
        return html
        

    def __get_time_str(self, epoch):
        try:
            s = time.strftime(self.prefs.get('TIME_STR'), time.localtime(epoch))
        except:
            s = ""
        return s


    def create_summary(self):
        if self.__verbose: print ">> Creating summary"
        report_dir = os.path.join(self.prefs.get('REPORT_DIR'),
                                   self.prefs.get('DATA_NAME'))

        summary = db.select_summary(self.cursor)

        self.__create_CSS(report_dir)
        
        html = "<html>\n<head>\n"
        html += '<meta http-equiv="Content-Type" content="text/html; charset=%s">\n' % self.prefs.get('CHARSET_ENCODING')
        html += "<title>Scratchy - %s</title>\n" % self.prefs.get('DATA_NAME')

        html += '<link href="%s" type="text/css" rel="stylesheet">' % self.css_name
       
        html += "</head>\n"
        html += "<body bgcolor=%s>\n" % self.prefs.get('COLOR_DEFAULT')

        html += self.get_template(self.prefs.get('TEMPLATE_SUMMARY'))
        html += "<table>"
                
        xhtml = "<table>"
        xhtml += self.__title_row("Date", 1)

        
        for data in summary:
            tm_tuple = (int(data['year']), int(data['month']), 0,0,0,0,0,0,0)
            try:
                epoch = time.mktime(tm_tuple)
                #summary.append(data)

                month = MONTHS.get(data['month']) + ", " + \
                        str(data['year'])

                label = """<a href=%s%s/index.html>%s</a>""" % \
                        (string.zfill(str(data['month']), 2), str(data['year']), month)

                xhtml += self.__data_row(label,
                                        data['hits'],
                                        data['pages'],
                                        get_kb(data['bytes']))

            except Exception, e:
                print e
                continue


        xhtml += "</table>"
        html = string.replace(html, "%% SUMMARY_TABLE %%", xhtml)
        if HAS_CHARTDIRECTOR:
            html = string.replace(html, "%% SUMMARY_CHART %%",
                                  '<img src=summary.png alt=""')
        else:
            html = string.replace(html, "%% SUMMARY_CHART %%", "")
            
        html += self.__get_scratchy_link("../")

        fp = open(os.path.join(report_dir, "index.html"), "w")
        fp.write(html)
        fp.close()

        if HAS_CHARTDIRECTOR:
            self.chart.create_summary_chart(os.path.join(os.pardir, "summary.png"),
                                            summary)

        
            

###################################################################################################

def usage():
    print
    print "Usage:"
    print sys.argv[0] + \
          " -m [1..12] | --month=[1..12] [-y year | --year=year] [ -c config | --config=config ] [ -d x | --debug=x] [-V]"
    print
    print "Prepare a report for the given month (and optionally year (defaults to current year)"
    print "Use the given config file (or the default config file if not supplied)"
    sys.exit(0)


if __name__ == '__main__':    
    config_file = "config"
    month = None
    year = time.localtime()[0]
    debug = 0

    args = sys.argv[1:]
    try:
        (opts, getopts) = getopt.getopt(args, 'd:m:y:c:?hV',
                                        ["month=", "debug=",
                                         "year=", "config=", "help"])
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
            #prefs = Prefs(config_file)
        if opt in ('-d', '--debug'):
            try:
                debug = int(arg)
            except:
                print "debug value must be an integer"
                usage()            
        if opt in ('-m', '--month'):
            try:
                month = int(arg)
                if month > 12 or month < 1: raise Exception
            except:
                print "month value must be an integer from 1 to 12"
                usage()
        if opt in ('-y', '--year'):
            try:
                year = int(arg)
            except:
                print "year value must be an integer"
                usage()


    if month and year and config_file:
        prefs = Prefs(config_file)
        r = Report(month, year, prefs)
        r.create_summary()
    else:
        usage()






