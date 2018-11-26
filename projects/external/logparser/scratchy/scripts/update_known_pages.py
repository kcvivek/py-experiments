#!/usr/bin/env python

import sys, os, string
import script_common

common = script_common.ScriptCommon()
prefs = common.prefs

common.execute('USE %s' % prefs.get('DATA_NAME'))

print "Setting all log.page records to 0"
common.execute("UPDATE log SET page = 0")

print "Setting log.page to 1 for all known page types"

known_pages = prefs.get('KNOWN_PAGES', 1)
if not known_pages:
    print "Exiting.  There are curently no known pages defined"
    sys.exit(0)
    
in_clause = ""
for kp in known_pages:
    in_clause += "'%s', " % kp
in_clause = in_clause[:-2]

sql = """
      SELECT file_type_id
      FROM file_type
      WHERE file_type IN (%s)
      """ % in_clause

common.execute(sql)

in_clause = ""
while 1:
    row = common.get_cursor().fetchone()
    if not row: break
    in_clause += "%d, " % row[0]
if in_clause: in_clause = in_clause[:-2]
else:
    print "No matching file_type_ids exist. Exiting"
    sys.exit(0)

sql = """
      UPDATE log
      SET page = 1
      WHERE file_type_id IN (%s)
      """ % in_clause

common.execute(sql)
print "Known pages updated"

