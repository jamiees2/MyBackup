from session import session as s
from urllib.parse import urlparse
import json
import os
from cgi import parse_header
import re
import shutil

def clearDir(folder):
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(e)

dirs = set()
def mkdir(base, name=None):
    if name:
        base = os.path.join(base, cleanFile(name))
    path = base
    i = 2
    # This way, it can be ensured that directories that shouldn't be there are
    # deleted
    while path in dirs:
        path = base + ("_%d" % i)
        i += 1
    dirs.add(path)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path

def cleanFile(value):
    return re.sub('[\\/:"*?<>|]+', '', value)

def stripQuery(url):
    return url.replace("?" + urlparse(url).query, "")

def save(path, url):
    data = s.get(url)
    if os.path.isdir(path):
        _, params = parse_header(data.headers["Content-Disposition"])
        with open(os.path.join(path, cleanFile(params["filename"])), "wb") as f:
            f.write(data.content)
    else:
        with open(path, 'wb') as f:
            f.write(data.content)

def jsondump(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)

html_tpl = """
<!doctype html>
<html>
<head>
<meta charset="utf8" />
<title>%s</title>
%s
<link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css" />
</head>
<body>
<div class="container">
%s
</div>
</body>
</html>
"""
def genHtml(path, data, title="", head=""):
    with open(path, "w") as f:
        f.write(html_tpl % (title, head, data))
def saveLink(path, link):
    genHtml(path, "", title="", head=("<script> window.location=\"%s\"</script>" % link ))
def saveRedirect(path, url):
    data = s.get(url, allow_redirects=False)
    saveLink(path, data.headers["Location"])
