
STATUSCODES = {
    200:'OK',                        
    201:'Created',
    202:'Request recorded, will be executed later',
    203:'Non-authoritative information',
    204:'Request executed',
    205:'Reset document',
    206:'Partial Content',
    
    300:'Multiple documents available',
    301:'Moved Permanently',
    302:'Found',
    303:'See other document',
    304:'Not Modified since last retrieval',
    305:'Use proxy', 
    306:'Switch proxy',
    307:'Document moved temporarily',
    
    400:'Bad Request',
    401:'Unauthorized',
    402:'Payment required',
    403:'Forbidden',
    404:'Document Not Found',
    405:'Method not allowed',
    406:'Document not acceptable to client',
    407:'Proxy authentication required',
    408:'Request Timeout',
    409:'Request conflicts with state of resource',
    410:'Document gone permanently',
    411:'Length required',
    412:'Precondition failed',
    413:'Request too long', 
    414:'Requested filename too long', 
    415:'Unsupported media type', 
    416:'Requested range not valid', 
    417:'Failed',
    500:'Internal server Error',
    501:'Not implemented',
    502:'Received bad response from real server',
    503:'Server busy',
    504:'Gateway timeout',
    505:'HTTP version not supported',
    506:'Redirection failed'
    }


def get_statuscode(code):
    return STATUSCODES.get(code, "Unknown")
    
