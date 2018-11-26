#  sql.py: -*- Python -*-  DESCRIPTIVE TEXT.
from types import StringType
import string

def getsql(sql, dict):
    """
    Return a sql statement using the SQL template passed in by applying
    the values from the dictionary.

    The dictionary should contain keys which match the tags in the SQL template.
    The template tags are specified by **tag_name** and the corresponding dictionary
    key would be 'tag_name'.

    # Example:

    # A sql template:
    >>> sql = 'SELECT * FROM table where col1 = **col1** and col2 = **col2**

    # The dictionary passed into getsql should contain keys for col1 and col2:
    >>> dict = {'col1': 'value_1',
                'col2': 'value_2'}

    >>> sqlstr = getget(sql, dict)
    >>> print sqlstr
    SELECT * FROM table where col1 = 'value_1' and col2 = 'value_2'
    """
    
    keys = dict.keys()
    for key in keys:
        s = "**%s**" % key
        r = dict.get(key)
        if r is None:
            r = "Null"
        elif type(r) is StringType:
            r = string.replace(r, "'", "\'")  # escape ticks w/ backslash-tick
            r = "'%s'" % r
        else:
            r = str(r)

        sql = string.replace(sql, s, r)
    return sql


SELECT_MAX_LOG_ID = """
SELECT MAX(log_id) AS num
FROM log
"""

SELECT_MAX_SESSION_ID = """
SELECT MAX(session_id) AS num
FROM session
"""

##INSERT_SESSION = """
##INSERT INTO session
##(session_id,
##ip_addr_id, session_start,
##session_end, session_duration,
##log_id_start, log_id_end, file_tracker_id)
##VALUES(**session_id**,
##**ip_addr_id**, **start**,
##**end**, **duration**,
##**log_id_start**, **log_id_end**, **file_tracker_id**)
##"""


INSERT_SESSION = """
INSERT INTO session
(session_id,
ip_addr_id, session_start,
session_end, session_duration,
month, year)
VALUES(**session_id**,
**ip_addr_id**, **session_start**,
**session_end**, **session_duration**,
**month**, **year**)
"""

SELECT_SUMMARY = """
SELECT SUM(page) AS pages,
           SUM(bytes) AS bytes,
           COUNT(*) AS hits,
           month,     
           year
FROM log
GROUP BY year, month
ORDER BY timestamp
"""
