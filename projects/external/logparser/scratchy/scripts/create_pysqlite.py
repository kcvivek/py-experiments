import sys, os, string
import script_common


common = script_common.ScriptCommon(0)
prefs = common.get_prefs()

clauses = (
    """
    CREATE TABLE ip_addr
    (ip_addr_id INT UNIQUE,
    ip_addr VARCHAR(16) PRIMARY KEY)
    """,
    """
    CREATE TABLE country
    (country_id INT UNIQUE,
    country VARCHAR(128) PRIMARY KEY)
    """,
    """
    CREATE TABLE url
    (url_id INT UNIQUE,
    url VARCHAR(128) PRIMARY KEY)
    """,
    """
    CREATE TABLE referer_domain
    (referer_domain_id INT UNIQUE,
    referer_domain VARCHAR(128) PRIMARY KEY)
    """,
    """
    CREATE TABLE referer_page
    (referer_page_id INT UNIQUE,
    referer_page VARCHAR(128) PRIMARY KEY)
    """,
    """
    CREATE TABLE referer_qs
    (referer_qs_id INT UNIQUE,
    referer_qs VARCHAR(255) PRIMARY KEY)
    """,
    """
    CREATE TABLE browser
    (browser_id INT UNIQUE,
    browser VARCHAR(128) ,
    version VARCHAR(16)  DEFAULT 'None',
    PRIMARY KEY(browser, version))
    """,
    """
    CREATE TABLE search_engine
    (search_engine_id INT,
    search_engine VARCHAR(128) ,
    PRIMARY KEY(search_engine),
    UNIQUE(search_engine_id))  
    """,
    """
    CREATE TABLE search_string
    (search_string_id INT,
    search_string VARCHAR(255) ,
    PRIMARY KEY(search_string),
    UNIQUE(search_string_id))  
    """,
    """
    CREATE TABLE search_keyword
    (search_keyword_id INT,
    search_keyword VARCHAR(128) ,
    PRIMARY KEY(search_keyword),
    UNIQUE(search_keyword_id))  
    """,
    """
    CREATE TABLE robot
    (robot_id INT,
    robot VARCHAR(128) ,
    PRIMARY KEY(robot),
    UNIQUE(robot_id))  
    """,
    """
    CREATE TABLE op_sys
    (op_sys_id INT,
    op_sys VARCHAR(128) ,
    version VARCHAR(16) ,
    PRIMARY KEY(op_sys, version),
    UNIQUE(op_sys_id))  
    """,
    """
    CREATE TABLE file_type
    (file_type_id INT,
    file_type VARCHAR(128) ,
    PRIMARY KEY(file_type),
    UNIQUE(file_type_id))  
    """,
    """
    CREATE TABLE log
    (log_id INT,
    timestamp INT ,
    page INT ,
    bytes INT ,
    status_code INT ,
    hour INT ,
    day_of_week INT ,
    day_of_month INT ,
    month INT ,
    year INT ,
    
    country_id INT ,
    referer_domain_id INT ,
    referer_page_id INT ,
    referer_qs_id INT ,
    url_id INT ,
    ip_addr_id INT ,
    op_sys_id INT ,
    robot_id INT ,
    search_engine_id INT ,
    search_string_id INT ,
    browser_id INT ,
    file_type_id INT ,
    UNIQUE(log_id)
    )  
    """,
    "CREATE INDEX timestamp_idx ON log (timestamp)", 
    "CREATE INDEX yearmonth_idx ON log (year, month)", 
    "CREATE INDEX country_idx ON log (country_id)", 
    "CREATE INDEX ref_dom_id_idx ON log(referer_domain_id)",
    "CREATE INDEX ref_pg_id_idx ON log(referer_page_id)",
    "CREATE INDEX ref_qs_id_idx ON log(referer_qs_id)",
    "CREATE INDEX url_id_idx ON log(url_id)",
    "CREATE INDEX ip_addr_id_idx ON log(ip_addr_id)",
    "CREATE INDEX op_sys_id_idx ON log(op_sys_id)",
    "CREATE INDEX robot_id_idx ON log(robot_id)",
    "CREATE INDEX srch_eng_id_idx ON log(search_engine_id)",
    "CREATE INDEX srch_str_id_idx ON log(search_string_id)",
    "CREATE INDEX browser_id_idx ON log(browser_id)",
    "CREATE INDEX file_type_id_idx ON log(file_type_id)",
    """
    CREATE TABLE session
    (session_id INT,
    ip_addr_id INT ,
    session_start INT ,
    session_end INT ,
    session_duration INT,
    log_id_start INT ,
    log_id_end INT ,

    UNIQUE(session_id))
    """,
    "CREATE INDEX sess_ip_addr_id_idx ON session (ip_addr_id)",
    "CREATE INDEX sess_log_id_start_idx ON session (log_id_start)",
    "CREATE INDEX sess_log_id_end_idx ON SESSION (log_id_end)",
    """
    CREATE TABLE search_keyword_log
    (search_keyword_log_id INT,
    search_keyword_id INT ,
    log_id INT ,

    PRIMARY KEY(search_keyword_id, log_id))
    """,
    "CREATE INDEX skl_skl_log_id_idx ON search_keyword_log (search_keyword_log_id)",
    "CREATE INDEX skl_log_id_idx ON search_keyword_log (log_id)",
)

insert_clauses = (
    """INSERT INTO referer_domain
    (referer_domain_id, referer_domain)
    VALUES(1, '-')
    """,
    """INSERT INTO referer_page
    (referer_page_id, referer_page)
    VALUES(1, '')
    """,
    """INSERT INTO referer_qs
    (referer_qs_id, referer_qs)
    VALUES(1, '')
    """,
    """INSERT INTO browser
    (browser_id, browser)
    VALUES(1, '')
    """,    
    """INSERT INTO robot
    (robot_id, robot)
    VALUES(1, '')
    """,    
    """INSERT INTO op_sys
    (op_sys_id, op_sys)
    VALUES(1, '')
    """,    

    """INSERT INTO search_engine
    (search_engine_id, search_engine)
    VALUES(1, '')
    """,    

    """INSERT INTO search_string
    (search_string_id, search_string)
    VALUES(1, '')
    """,    
    )
    

########################################################################


drive, path = os.path.splitdrive(os.getcwd())

datadir = prefs.get("DATA_DIR")
drive, path = os.path.splitdrive(datadir)
if path[0] != os.sep:
    path = os.path.join(os.pardir, path)
    

dbname = prefs.get("DATA_NAME")

dbpath = os.path.join(path, dbname, prefs.get('SQLITE_DB'))

if common.get_drop_db():
    print "Dropping database: %s" % dbname
    try:
        os.remove(dbpath)
    except:
        pass

print "Creating Scratchy database %s (if necessary)" % dbname

#dbconnection = sqlite.connect(dbpath, 774)
dbconnection = common.connect(dbpath)

db = dbconnection.cursor()

#print "connection: ", dir(dbconnection)
#print "cursor:", dir(db)
print "Creating Scratchy tables for %s database" % dbname

for clause in clauses:
    try:
        db.execute(clause)
    except Exception, e:
        print str(e)
        print clause
        sys.exit(0)

for clause in insert_clauses:
    try:
        db.execute(clause)
    except Exception, e:
        if e[0] != 1062:  # 1062 = duplicate
            print clause
            print str(e)
        sys.exit(0)

dbconnection.commit()
dbconnection.close()
