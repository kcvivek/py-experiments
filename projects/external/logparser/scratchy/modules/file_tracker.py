
import os, os.path, sys, string, time
from file_base import FileBase

class FileTracker:
    def __init__(self, cursor, escape_tick):
        self.cursor = cursor
        self.escape_tick = escape_tick

    def get(self, first_line):
        sql = """
        SELECT file_tracker_id,
               file_size,
               file_offset
        FROM   file_tracker
        WHERE  first_line = '%s'
        """ % self.escape_tick.escape_str(first_line)
               
        self.cursor.execute(sql)

        return self.cursor.fetchone()
                

    def insert(self, first_line, file_size):
        file_tracker_id = self.get_next_id()
        sql = """
        INSERT INTO file_tracker
        (file_tracker_id, first_line, file_size, parsed_timestamp)
        VALUES ('%d', '%s', '%d', '%ld')
        """ % (file_tracker_id,
               self.escape_tick.escape_str(first_line),
               file_size,
               time.time())
        
        self.cursor.execute(sql)
        return file_tracker_id

        
    def set(self, first_line, file_size, file_offset):
        existing_row = self.get(first_line)
        if existing_row:
            sql = """
            UPDATE file_tracker
            SET    file_size = '%d',
                   file_offset = '%d',
                   parsed_timestamp = '%ld'
            WHERE  file_tracker_id = '%d'
            """ % (file_size, file_offset, time.time(), existing_row['file_tracker_id'])
            self.cursor.execute(sql)
        else:
            self.insert(first_line, file_size)


    def get_next_id(self):
        sql = """
        SELECT MAX(file_tracker_id) AS num
        FROM file_tracker
        """

        self.cursor.execute(sql)
        try:
            return self.cursor.fetchone()['num'] + 1
        except:
            return 1
