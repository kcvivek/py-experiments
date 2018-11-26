
class SQLInit:
    def __init__(self):
        pass

    def get_create_clauses(self):
        raise Exception, "not implemented"

    def get_insert_clauses(self):
        raise Exception, "not implemented"


class MySQLInit(SQLInit):
    def __init__(self, dbname=None):
        self.dbname = dbname
        
    def set_db_name(self, dbname):
        self.dbname = dbname

    def get_create_clauses(self):
        return (
            "CREATE DATABASE IF NOT EXISTS %s" % self.dbname,
            "USE %s" % self.dbname,
            """
-- THIS WILL FAIL ON MYSQL VERSION 3.x -- THIS IS SAFE TO IGNORE!!! --
            
            CREATE TABLE IF NOT EXISTS file_tracker
            (file_tracker_id INT,
            file_size INT NOT NULL,
            file_offset INT,
            parsed_timestamp BIGINT,
            first_line TEXT(1000) NOT NULL,
            PRIMARY KEY(first_line(1000)),
            KEY(file_tracker_id))  TYPE=MyISAM
-- THIS WILL FAIL ON MYSQL VERSION 3.x -- THIS IS SAFE TO IGNORE!!! --          
            """,
            """
            CREATE TABLE IF NOT EXISTS file_tracker
            (file_tracker_id INT,
            file_size INT NOT NULL,
            file_offset INT,
            parsed_timestamp BIGINT,
            first_line VARCHAR(255) NOT NULL,
            PRIMARY KEY(first_line),
            KEY(file_tracker_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS ip_addr
            (ip_addr_id INT,
            ip_addr CHAR(16) NOT NULL,
            hostname VARCHAR(255) NOT NULL,
            PRIMARY KEY(ip_addr, hostname),
            KEY(ip_addr_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS country
            (country_id INT,
            country VARCHAR(128) NOT NULL,
            PRIMARY KEY(country),
            KEY(country_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS url
            (url_id INT,
            url VARCHAR(128) NOT NULL,
            PRIMARY KEY(url),
            KEY(url_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS referer_domain
            (referer_domain_id INT,
            referer_domain VARCHAR(128) NOT NULL,
            PRIMARY KEY(referer_domain),
            KEY(referer_domain_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS referer_page
            (referer_page_id INT,
            referer_page VARCHAR(128) NOT NULL,
            PRIMARY KEY(referer_page),
            KEY(referer_page_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS referer_qs
            (referer_qs_id INT,
            referer_qs VARCHAR(255) NOT NULL,
            PRIMARY KEY(referer_qs),
            KEY(referer_qs_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS browser
            (browser_id INT,
            browser VARCHAR(128) NOT NULL,
            version VARCHAR(16) NOT NULL DEFAULT '',
            PRIMARY KEY(browser, version),
            KEY(browser_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS search_engine
            (search_engine_id INT,
            search_engine VARCHAR(128) NOT NULL,
            PRIMARY KEY(search_engine),
            KEY(search_engine_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS search_string
            (search_string_id INT,
            search_string VARCHAR(255) NOT NULL,
            PRIMARY KEY(search_string),
            KEY(search_string_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS search_keyword
            (search_keyword_id INT,
            search_keyword VARCHAR(128) NOT NULL,
            PRIMARY KEY(search_keyword),
            KEY(search_keyword_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS robot
            (robot_id INT,
            robot VARCHAR(128) NOT NULL,
            PRIMARY KEY(robot),
            KEY(robot_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS op_sys
            (op_sys_id INT,
            op_sys VARCHAR(128) NOT NULL,
            version VARCHAR(16) NOT NULL,
            PRIMARY KEY(op_sys, version),
            KEY(op_sys_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS file_type
            (file_type_id INT,
            file_type VARCHAR(128) NOT NULL,
            PRIMARY KEY(file_type),
            KEY(file_type_id))  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS log
            (log_id INT,
            timestamp INT NOT NULL,
            page INT NOT NULL,
            bytes INT NOT NULL,
            status_code INT NOT NULL,
            hour INT NOT NULL,
            day_of_week INT NOT NULL,
            day_of_month INT NOT NULL,
            month INT NOT NULL,
            year INT NOT NULL,

            file_tracker_id INT NOT NULL,
            country_id INT NOT NULL,
            referer_domain_id INT NOT NULL,
            referer_page_id INT NOT NULL,
            referer_qs_id INT NOT NULL,
            url_id INT NOT NULL,
            ip_addr_id INT NOT NULL,
            op_sys_id INT NOT NULL,
            robot_id INT NOT NULL,
            search_engine_id INT NOT NULL,
            search_string_id INT NOT NULL,
            browser_id INT NOT NULL,
            file_type_id INT NOT NULL,
            
            KEY(log_id),
            KEY(file_tracker_id),
            KEY(timestamp),
            KEY(year, month),
            KEY(country_id),
            KEY(referer_domain_id),
            KEY(referer_page_id),
            KEY(referer_qs_id),
            KEY(url_id),
            KEY(ip_addr_id),
            KEY(op_sys_id),
            KEY(robot_id),
            KEY(search_engine_id),
            KEY(search_string_id),
            KEY(browser_id),
            KEY(file_type_id)
            )  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS session
            (session_id INT AUTO_INCREMENT,
            ip_addr_id INT NOT NULL,
            session_start INT NOT NULL,
            session_end INT NOT NULL,
            session_duration INT NOT NULL,
            month INT NOT NULL,
            year INT NOT NULL,
--            log_id_start INT NOT NULL,
--            log_id_end INT NOT NULL,
--            file_tracker_id INT NOT NULL,
            
            KEY(session_id),    
            KEY(ip_addr_id),
--            KEY(log_id_start),
--            KEY(log_id_end),
--            KEY(file_tracker_id),
            KEY(month, year)
            )  TYPE=MyISAM  
            """,
            """
            CREATE TABLE IF NOT EXISTS search_keyword_log
            (search_keyword_log_id INT,
            search_keyword_id INT NOT NULL,
            log_id INT NOT NULL,
            
            PRIMARY KEY(search_keyword_id, log_id),
            KEY(search_keyword_log_id),
            KEY(log_id)
            )  TYPE=MyISAM  
            """,)

    def get_insert_clauses(self):
        return (
            """INSERT INTO referer_domain
            (referer_domain_id, referer_domain)
            VALUES(0, '-')
            """,
            """INSERT INTO referer_page
            (referer_page_id, referer_page)
            VALUES(0, '')
            """,
            """INSERT INTO referer_qs
            (referer_qs_id, referer_qs)
            VALUES(0, '')
            """,
            """INSERT INTO browser
            (browser_id, browser)
            VALUES(0, '')
            """,    
            """INSERT INTO robot
            (robot_id, robot)
            VALUES(0, '')
            """,    
            """INSERT INTO op_sys
            (op_sys_id, op_sys)
            VALUES(0, '')
            """,    
            
            """INSERT INTO search_engine
            (search_engine_id, search_engine)
            VALUES(0, '')
            """,    
            
            """INSERT INTO search_string
            (search_string_id, search_string)
            VALUES(0, '')
            """,    
            
            """INSERT INTO country
            (country_id, country)
            VALUES(0, '')
            """,         
            )
            
            
class SQLiteInit(SQLInit):
    def __init__(self):
        pass

    def get_create_clauses(self):
        return (
            """
            CREATE TABLE file_tracker
            (file_tracker_id INT UNIQUE,
            file_size INT NOT NULL,
            file_offset INT,
            parsed_timestamp BIGINT,
            first_line VARCHAR(1000) NOT NULL PRIMARY KEY)
            """,
            "CREATE INDEX file_tracker_idx ON file_tracker (file_tracker_id)", 
            """
            CREATE TABLE ip_addr
            (ip_addr_id INT UNIQUE,
            ip_addr VARCHAR(16) NOT NULL
            hostname VARCHAR(255) NOT NULL,
            PRIMARY KEY (ip_addr, hostname))
            """,
            "CREATE INDEX ip_addr_idx ON ip_addr (hostname)",
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

            file_tracker_id INT ,
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
            "CREATE INDEX ft_idx ON log (file_tracker_id)", 
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
            file_tracker_id INT,
            
            UNIQUE(session_id))
            """,
            "CREATE INDEX sess_ip_addr_id_idx ON session (ip_addr_id)",
            "CREATE INDEX sess_log_id_start_idx ON session (log_id_start)",
            "CREATE INDEX sess_log_id_end_idx ON SESSION (log_id_end)",
            "CREATE INDEX sess_ft_id_idx ON SESSION (file_tracker_id)",
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

    def get_insert_clauses(self):
        return (
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
