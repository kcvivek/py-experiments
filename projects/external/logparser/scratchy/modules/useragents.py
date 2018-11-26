import re

winie_re = re.compile(r""".*? (?P<browser>MSIE) (?P<version>[0-9\.]*).*? (?P<os>Win(?:dows)?(?: NT)?) ?(?P<osvers>Me|XP|[0-9\.]*)""")


special_browsers = (
    re.compile(r"""(?P<browser>konqueror)/(?P<version>.*?);"""),
    re.compile(r"""(?P<browser>safari)/(?P<version>.*)"""),
    re.compile(r"""(?P<browser>opera)/(?P<version>[\d|\.]*)"""),
#    re.compile(r"""(?P<browser>ms ?frontpage(wpp)?)[ |/](?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>galeon)/(?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>netscape)\d*/(?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>msie)[ |_|/](?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>links) \((?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>firefox)/(?P<version>[\d|\.]*)"""),
    re.compile(r"""(?P<browser>avant browser)"""),
    re.compile(r"""(?P<browser>advanced browser)"""),
    ##### NOTE: Mozilla must be after all Mozilla compatibles ####
#    re.compile(r"""(?P<browser>Mozilla)[/| ](?P<version>[\d|\.]*)"""),  
    )

opsys_re = re.compile(r"""Windows NT 5.0|WinNT|Win95|Win98|Windows-NT|Windows 95|Win 9x 4.90|Windows 2000|Macintosh|Mac_PowerPC|Mac_PPC|Linux|OSIX|SunOS|WebTV""")
                      


# innerprisebot|psbot|msnbot|surveybot|iconsurf|almaden|obot|nextopiabot|webrescuer"""


generic_browser_re = re.compile(r"""(?P<browser>[a-z0-9\-]*)[\s\-_/]*(?P<version>[0-9\.]*)""")

OPERATING_SYS = {
    'Windows NT 5.1': 'Windows XP',
    'Windows NT 5.0': 'Windows 2000',
    'Windows 2000': 'Windows 2000',
    'Windows NT 3.11': 'Windows NT',
    'Windows NT 4.0': 'Windows NT',
    'Windows NT': 'Windows NT',
    'Windows-NT': 'Windows NT',
    'Windows 95': 'Windows 95',
    'Windows 98': 'Windows 98',
    'WinNT': 'Windows NT',
    'Win95': 'Windows 95',
    'Win98': 'Windows 98',
    'Windows 3.11': 'Windows 3.11',
    'X11': 'Unix',
    'SunOS': 'Unix',
    'Linux': 'Linux',
    'WebTV': 'Web TV',
    'OSIX': 'Macintosh',
    'Macintosh': 'Macintosh',
    'Mac_PPC': 'Macintosh',
    'Mac_PowerPC': 'Macintosh',
    }

ROBOTS = {
    'googlebot': 'Google',
    'ask jeeves': 'Ask jeeves',
    'slurp@inktomi': 'Inktomi',
    'crawler@fast.no': 'Fast',
    'zyborg@wisenutbot.com': 'Wise Nut',
    'truerobot': 'Echo.com',
    'ia_archiver': 'Alexa',
    'latnet-search-engine': 'TVNet',
    'diibot': 'Digital Integrity',
    'mercator_': "AltaVista",
    'mercator-': "AltaVista",
    'www.first-search.com': 'Galaxy',
    'linkwalker': 'seventwentyfour.com',
    'lycos_spider': 'Lycos',
    'scooter-': 'AltaVista',
    'zcraft-query@zeus.com': 'Zeus',
    'architextspider': 'Excite',
    'ru-robot': 'Rutgers University',
    'linksweeper': 'LinkSweeper',
    '@teoma.com': 'Teoma',
    'atSpider': 'atSpider',
    'daviesbot': 'www.wholeweb.net',
    'surfairy': 'Surfairy',
    'openfind': 'Openfind',
    'webcopier': 'WebCopier',
    'cosmos': 'xyleme.com',
    'gulliver': 'NorthernLight',
    'flashget': 'FlashGet',
    'larbin_': 'complete.com',
    'npbot': 'NameProtext',
    'SietsCrawler': 'Siets',
    'mylinea.com Checker': 'Mylinea.com',
    'microsoftprototypecrawler': 'Microsoft',
    'msnbot': "Microsoft",
    'naverrobot': 'NaverRobot',
    'surveybot': 'SurveyBot',
    'innerprisebot': 'InnerpriseBot',
    'psbot': 'PSBot',
    'iconsurf': 'IconSurf',
    'www.almaden.ibm.com': 'IBM Almaden',
    'obot': 'oBot',
    'nextopiabot': 'NextopiaBot',
    'webrescuer': 'WebRescuer',
    'yahoo-mmcrawler': 'Yahoo-MMCrawler',
    }

BROWSERS = {
    'msie': 'Internet Explorer',
    'firefox': 'FireFox',
    'mozilla': 'Mozilla',
    'netscape': 'Netscape',
    'opera': 'Opera',
    'safari': 'Safari',
    'konqueror': 'Konqueror',
    'accs url': 'Accs URL',
    'gnome-vfs': 'gnome-vfs',
    'macnetwork': 'MacNetwork',
    'ssc_url' : 'ssc_url',
    'url_access': 'URL Access',
    'url Access': 'URL Access',
    'accs_url': 'Accs URL',
    'accs URL': 'Accs URL',
    'cfnetwork': 'CFNetwork',
    'apple-cfnetwork': 'CFNetwork',
    'cafi': 'Cafi',
    'ms frontpage': 'FrontPage',
    'msfrontpage':  'FrontPage',
    'msfrontpagewpp':  'FrontPage',
    'apachebench': 'ApacheBench',
    "galeon": "Galeon",
    'links': 'Links',
    'zeus': 'Zeus',
    'contype': 'contype',
    'microsoft-webdav-miniredir': 'Microsoft-WebDAV-MiniRedir',
    'microsoft data access internet publishing provider dav': 'Microsoft Data Access Internet Publishing Provider DAV',
    'lynx': 'Lynx',
    'teleport pro': 'Teleport Pro',
    'rpt-httpclient': 'RPT-HTTPClient',
    'scooter_mercator': 'Scooter_Mercator',
    'expressloader': 'LapLink ExpressLoader',
    'siegepipe': 'Siegepipe',
    'eudora': 'Eudora',
    'justview': 'JustView',
    'offline explorer': 'Offline Explorer',
    'exmh html browser': 'Exmh HTML Browser',
    'internet ninja': 'Internet Ninja',
    'miixpc': 'MIIxpc',
    'java': 'Java',
    'pockey': 'Pockey',
    'webrow': 'WEBROW',
    'webzip': 'WebZIP',
    'lwp::simple': 'Perl',
    'libwww-perl': 'Perl',
    'ip*works!': 'IP*Works!',
    'disco pump': 'DISCo Pump',
    'microsoft url control': 'Microsoft URL Control',
    'xmms': 'Xmms',
    'winampmpeg': 'WinampMPEG',
    'calzilla': 'Calzilla',
    'python-urllib': 'Python-urllib',
    'wget': 'Wget',
    'windows-media-player': 'Windows-Media-Player',
    'nsplayer': 'NSPlayer',
    'webfetch': 'WebFetch',
    'echoping': 'Echoping',
    'curl': 'curl',
    'dillo': 'Dillo',
    'website quester': 'Website Quester',
    'advanced browser': 'Avant Browser',
    'avant browser': 'Avant Browser',
    }


def get_robots_regex():
    robot_re = '|'.join(ROBOTS.keys())
    robot_re = robot_re.replace(".", "\.")
    return re.compile(robot_re)
        

def parse_special_browser(useragent):
    for regex in special_browsers:
        m = regex.search(useragent)

        if m:
            #print "found browser:", m.group('browser'), "-",  m.group('version')
            try:
                vers = m.group('version')
            except:
                vers = ""
            return (m.group('browser'), vers)

    return None
