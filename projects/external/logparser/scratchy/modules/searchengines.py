#
# hash table of search engines.  Each key is the base url for the
# search engine (referer) and each value is a hash table with it's
# formal name and the query param (search string)
#
# NOTE: the base url is considered to be the relevent portion of the engine
# domain.  In general, "www." and last entity (eg. .com) are removed
#   eg. www.google.com => google
#   eg. images.google.com => images.google
#   eg. www.google.ca => google
#   eg. googe.com => google

SearchEngines = {
    'google': {'name': 'Google',
                       'param': 'q'},

    'images.google': {'name': 'Google Image Search',
                      'param': 'q'},

    'search.metacrawler': {'name': 'MetaCrawler',
                           'param': 'general'},
    
    'search.iwon': {'name': 'iWon',
                    'param': "searchfor"},

    'worldnet.att' : {'name': 'AT&T',
                      'param': 'qry'},

    'search.excite' : {'name': 'Excite',
                       'param': 's'},

    'lycos': {'name': 'Lycos',
              'param': 'query'},

    'altavista': {'name': 'AltaVista',
                  'param': 'q'},

    'dogpile': {'name': 'Dogpile',
                'param': 'qkw'},

    'wisenut': {'name': 'WiseNut',
                'param': 'q'},

    's.teoma': {'name': 'Teoma',
                'param': 'q'},

    'hotbot': {'name': 'HotBot',
               'param': 'query'},

    'savvy': {'name': 'Savvy',
              'param': 's'},

    'search': {'name': 'Search.com',
               'param': 'q'},

    'search.yahoo': {'name': 'Yahoo',
                     'param': 'p'},

    'search.netscape': {'name': 'Netscape',
                        'param': 'query'},

    'search.aol': {'name': 'AOL',
                   'param': 'query'},

    'search.msn': {'name': 'MSN',
                   'param': 'q'},

    'overture': {'name': 'Overture',
                 'param': 'Keywords'},
    
    'looksmart': {'name': 'LookSmart',
                  'param': 'key'},

    'search.tvnet': {'name': 'TVNET',
                     'param': 'q'},
    
    'siets': {'name': 'Siets',
              'param': 'query'}, 

    'w.galaxy': {'name': 'Galaxy',
                 'param': 'k'},

    'alexa': {'name': 'Alexa',
              'param': 'q'},

    'alltheweb': {'name': 'AllTheWeb',
         'param': 'q'},
    
    'a9': {'name': 'a9',
         'param': ''},
    
    'dmoz': {'name': 'dmoz',
         'param': 'search'},
    
    'terra': {'name': 'Terra',
         'param': 'query'},
    
    'voila': {'name': 'Voila',
         'param': 'kw'},
    
    'sympatico': {'name': 'Sympatico',
                  'param': 'query'},

    'go': {'name': 'Go',
         'param': 'qt'},

    'ask': {'name': 'Ask Jeeves',
         'param': 'ask'},

    'atomz': {'name': 'Atomz',
         'param': 'sp-q'},

    'euroseek': {'name': 'EuroSeek',
                 'param': 'query'},

    'findarticles': {'name': 'FindArticls',
                     'param': 'key'},

    'go2net': {'name': 'Go2Net',
               'param': 'general'},

    'infospace': {'name': 'InfoSpace',
                  'param': 'qkw'},

    'kvasir': {'name': 'kvasir',
         'param': 'q'},

    'mamma': {'name': 'Mamma',
         'param': 'query'},

    'nbci': {'name': 'nbci',
             'param': 'keyword'},

    'northernlight': {'name': 'Northern Light',
                      'param': 'qr'},

    'overture': {'name': 'Overture',
         'param': 'keywords'},

    'spray': {'name': 'Spray',
         'param': 'string'},

    'webcrawler': {'name': 'WebCrawler',
                   'param': 'searchText'},

    'ixquick': {'name': 'ix quick',
                'param': 'query'},

    'earthlink': {'name': 'Earthlink',
                  'param': 'q'},

    'i-une': {'name': 'i-une',
              'param': 'q'},
    
##    '': {'name': '',
##         'param': ''},


    }



