import os
import sys
import string
import re
try:
    import cPickle as pickle
except:
    import pickle

MYSQL  = 0
SQLITE = 1
GADFLY = 2


LOG_STRUCT = {'summary': {'month': None,
                          'year': None,
                          'bytes': 0,
                          #'parsed_lines': 0,
                          #'total_lines': 0,
                          'pages': 0,
                          'hits': 0},
              'date': {},
              'day_of_week': {},
              'hour': {},
              'host': {},
              'page': {},
              'code': {},
              'file_type': {},
              'error_page': {},
              'error_code': {},
              'referer': {},
              'visit': {},
              'session': {},
              'search_engine': {},
              'search_string': {},
              'search_keyword': {},
              'external_link': {},
              'opsys': {},
              'robot': {},
              'browser': {},
              'browser_vers': {},
              'ip_trace': {},
              'country': {},
              }

MONTHS = {1: 'January',
          2: 'February',
          3: 'March',
          4: 'April',
          5: 'May',
          6: 'June',
          7: 'July',
          8: 'August',
          9: 'September',
          10: 'October',
          11: 'November',
          12: 'December'
          }

DAYS = {0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"}

NUM_FORMAT_COMPILE = re.compile("[0-9][0-9][0-9][0-9][\.\,$]")

def get_filename(prefs, month, year):
    return prefs.get('DATA_DIR') + os.sep + prefs.get('DATA_NAME') + os.sep + \
           string.zfill(month, 2) + str(year)

def get_reportdir(prefs, month, year):
    return prefs.get('REPORT_DIR') + os.sep + prefs.get('DATA_NAME') + os.sep + \
           string.zfill(month, 2) + str(year)

def get_reportname(prefs, month, year):
    return get_reportdir(prefs, month, year) + os.sep + "index.html"    
            
        
def save_pickle(filename, parsed_data):
    try:
        fp = open(filename, "w")
    except:
        print "Could not write file:", filename
        return None

    #print "write:", parsed_data['summary']
    p = pickle.Pickler(fp)
    p.dump(parsed_data)
    fp.close()


def read_pickle(filename):
    try:
        fp = open(filename, "r")
    except:
        print "Could not read file:", filename
        return None

    u = pickle.Unpickler(fp)
    parsed_data = u.load()
    fp.close()
    #print "read", parsed_data['summary']
    return parsed_data



def format_number(num, sep=",", format_under_10k=0):
    # return a string representing the number by inserting
    # commas (or SEP chars) for readability.
    #
    # if format_under_10k is true, then numbers 1000 - 9999 will
    # be rewritten as 1,000 - 9,999
    s = str(num)

    if num < 1000:
        return s
    
    if not format_under_10k and num < 9999:
        return s

    idx = string.find(s, ".")
    if idx > -1:
        deci = s[idx:]
        s = s[:idx]
    else:
        deci = None
        

    lst = list(s)
    lst.reverse()

    count = range(3, len(lst),  3)
    count.reverse()
    for i in count:
        lst.insert(i, sep)

    lst.reverse()
    s = ''.join(lst)

    if deci: s += deci
    return s


def get_kb(bytes):
    return int(bytes or 0) / 1024

        
def get_range(lst, num):
    # if num = 0 -> range is the entire list
    # if num > 0 -> range is the minimum of the entire list or num
    if not num: r = len(lst)
    else:       r = min(len(lst), num)
    return r


def makedirs(path):
    try:
        os.makedirs(path, 0700)
    except OSError, e:
        if e.args[0] != 17: # 17 = directory exists (which we can ignore)
            print e
            sys.exit(0)
    except Exception, e:
        print e
        sys.exit(0)

