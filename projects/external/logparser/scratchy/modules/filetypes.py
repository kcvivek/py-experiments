
import string

FILETYPES = {
    'gif': 'Image',
    'png': 'Image',
    'jpg': 'Image',
    'bmp': 'Image',
    'tif': 'Image',
    'tiff': 'Image',
    'pdf': 'Document (PDF)',
    'jpeg': 'Image',
    'html': 'Web page',
    'htm': 'Web page',
    'cgi': 'Script (CGI)',
    'doc': 'Document (Word)',
    'xls': 'Spreadsheet (Excel)',
    'py' : "Script (Python)",
    'php': "Script (PHP)",
    'php3': "Script (PHP)",
    'pl' : "Script (Perl)",
    'spy': "Script (Spyce)",
    'exe': 'Executable (Windows)',
    'ico': 'Image (icon)',
    'txt': 'Document (text)',
    'swf': 'Flash Animation',
    'css': 'Cascading Style Sheet',
    'wmv': 'Video (Windows Media)',
    'wma': 'Audio (Windows Media)',
    'mp3': 'Audio (MP3)',
    'ra': 'Audio (Real)',
    'ram': 'Audio (Real)',
    'zip': 'Compressed (zip)',
    'gz': 'Compressed (GNU zip)',
    'bz2': 'Compressed',
    'rar': 'Compressed',
    'avi': 'Video (AVI)',
    'mpg': 'Video (MPEG)',
    'mpeg': 'Video (MPEG)',
    'sh': 'Shell script',
    'jar': 'Compressed (Java)',
    'tar': 'Archive (tar)',
    'ppt': 'Presentation (Powerpoint)',
    'pps': 'Presentation (Powerpoint)',
    'xml': 'Web page (XML)',
    'dll': 'Library (Windows)',
    'so' : 'Library (Linux)',
    'rpm': 'Compressed (Linux)',
    'deb': 'Compressed (Linux)',
    'js': 'Script (Javascript)',
    'asp': 'Script (ASP)',
    'jsp': 'Script (JSP)',
    'phtml': 'Script (Perl)',
    'wav': 'Audio',
    'au': 'Audio',
    'rm': 'Audio (Real)',
    'cab': 'Compressed (Windows)',
    }

def get_filetype(suffix):
    if suffix:
        suffix = string.lower(suffix)
    return FILETYPES.get(suffix, "Unknown")





