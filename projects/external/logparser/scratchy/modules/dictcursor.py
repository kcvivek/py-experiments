
class DictCursor:
    def __init__(self, connection):
        print "DictCursor.__init__"
        self.connection = connection
        self.cursor = connection.cursor()
        
        self.execute = self.cursor.execute
        self.__col_map = {}

    def __set_col_map(self):
        self.__col_map = {}
        desc = self.cursor.description
        for i in range(len(desc)):
            col = desc[i][0]
            self.__col_map[col.lower()] = i

        
    def fetchone(self):
        print "DictCursor.fetchone()"
        results = self.cursor.fetchone()
        self.__set_col_map()
        return DictResult(results, self.__col_map)


    def fetchall(self):
        print "DictCursor.fetchall()"
        results = self.cursor.fetchall()
        self.__set_col_map()
        return [DictResult(r, self.__col_map) for r in results]

    def fetchmany(self, num=None):
        print "DictCursor.fetchmany(" + str(num) + ")"
        results = self.cursor.fetchmany(num)
        self.__set_col_map()
        return [DictResult(r, self.__col_map) for r in results]


        

class DictResult:
    def __init__(self, results, col_map):
        self.__results = results
        self.__col_map = col_map

    def __getitem__(self, key):
        return self.__results[self.__col_map[key]]

    def get(self, key, notfound=None):
        try:
            return self.__results[self.__col_map[key]]
        except:
            return notfound

    def __repr__(self):
        return self.__col_map.keys()

    def __str__(self):
        return str(self.__col_map.keys())
    
        
if __name__ == '__main__':
    import gadfly

    conn = gadfly.gadfly("phil", "../data/phil")
    #cursor = conn.cursor()
    cursor = DictCursor(conn)
    
    sql = "SELECT * FROM log"

    cursor.execute(sql)
    rs = cursor.fetchone()

    print "---------------------------------"
    print rs.get('timestamp')
    print rs['timestamp']
    print "---------------------------------"

    rows = cursor.fetchmany(3)
    for row in rows:
        print row['log_id']

    print "---------------------------------"
    rows = cursor.fetchall()
    for row in rows:
        print row['url_id']
        break



    sql = """SELECT SUM(page) AS pages,
           SUM(bytes) AS bytes,
           COUNT(*) AS hits
           FROM log
           WHERE timestamp >= 1049184000
           AND timestamp <= 1051775940
           """

    cursor.execute(sql)
    row = cursor.fetchone()
    print row
    print row['hits']


    sql = """SELECT COUNT(*) AS hits, SUM(page) AS pages, SUM(bytes) AS bytes, url
    FROM url, log
    WHERE url.url_id = log.url_id
    AND timestamp >= 1049184000 AND timestamp <= 1051775940 AND page = 1 
    GROUP BY url
    ORDER BY SUM(page)
    """

    sql = """SELECT page AS pages
    FROM log
    ORDER BY pages
    """


    cursor.execute(sql)

    #row = cursor.fetchone()
    #print row
    #print row['hits']
